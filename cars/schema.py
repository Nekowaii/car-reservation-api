import graphene
from graphene_django import DjangoObjectType
from django.utils.timezone import now
from cars.models import Branch, Car, Reservation, CarBranchLog, Distance
from cars.utils import total_minutes
from cars.car_search import find_available_car
import datetime
from django.db.models import OuterRef, Subquery, Max, IntegerField, BigAutoField, F
from django.db.models.functions import Coalesce
from graphql import GraphQLError


class BranchType(DjangoObjectType):
    class Meta:
        model = Branch
        fields = ["id", "city"]


class BranchInput(graphene.InputObjectType):
    city = graphene.String(required=True)


class CarType(DjangoObjectType):
    current_branch = graphene.Field(BranchType)

    class Meta:
        model = Car
        fields = ["id", "car_number", "make", "model"]

    # def resolve_current_branch(self, info):
    #    return (
    #        CarBranchLog.objects.historical(end_time=now())
    #        .filter(car=self)
    #        .first()
    #        .branch
    #    )


class CreateCarInput(graphene.InputObjectType):
    car_number = graphene.String(required=True)
    make = graphene.String(required=True)
    model = graphene.String(required=True)
    branch = BranchInput(required=True)


class CarBranchLogType(DjangoObjectType):
    class Meta:
        model = CarBranchLog
        fields = ["id", "car", "branch", "timestamp"]


class CreateCar(graphene.Mutation):
    class Arguments:
        car_data = CreateCarInput(required=True)

    car = graphene.Field(CarType)
    car_branch_log = graphene.Field(CarBranchLogType)

    @staticmethod
    def mutate(root, info, car_data):
        branch = Branch.objects.get(city=car_data.branch.city)
        car = Car.objects.create(
            car_number=car_data.car_number, make=car_data.make, model=car_data.model
        )
        car_branch_log = CarBranchLog.objects.create(
            car=car, branch=branch, timestamp=now()
        )
        return CreateCar(car=car, car_branch_log=car_branch_log)


class DeleteCar(graphene.Mutation):
    class Arguments:
        car_number = graphene.String(required=True)

    ok = graphene.Boolean()

    @staticmethod
    def mutate(root, info, car_number):
        car = Car.objects.get(car_number=car_number)

        if Reservation.objects.reserved_now(car):
            raise GraphQLError("Can't delete a car that is reserved now.")

        car.delete()

        return DeleteCar(ok=True)


class UpdateCarInput(graphene.InputObjectType):
    car_number = graphene.String(required=True)
    make = graphene.String(required=True)
    model = graphene.String(required=True)


class UpdateCar(graphene.Mutation):
    class Arguments:
        car_data = UpdateCarInput(required=True)

    car = graphene.Field(CarType)

    @staticmethod
    def mutate(root, info, car_data):
        car = Car.objects.get(car_number=car_data.car_number)

        if Reservation.objects.reserved_now(car):
            raise GraphQLError("Can't update a car that is reserved now.")

        car.make = car_data.make
        car.model = car_data.model

        return UpdateCar(car=car)


class ReservationType(DjangoObjectType):
    class Meta:
        model = Reservation
        fields = [
            "id",
            "car",
            "start_time",
            "end_time",
            "pickup_branch",
            "return_branch",
        ]


class ReservationInput(graphene.InputObjectType):
    start_time = graphene.DateTime(required=True)
    duration_minutes = graphene.Int(required=True)
    pickup_branch = BranchInput(required=True)
    return_branch = BranchInput(required=True)


class CreateReservation(graphene.Mutation):
    class Arguments:
        reservation_data = ReservationInput(required=True)

    # reservation = graphene.Field(ReservationType)
    ok = graphene.Boolean()
    reservation = graphene.Field(ReservationType)

    @classmethod
    def mutate(cls, root, info, reservation_data):
        pickup_branch = Branch.objects.get(city=reservation_data.pickup_branch.city)
        return_branch = Branch.objects.get(city=reservation_data.return_branch.city)
        duration_time = datetime.timedelta(minutes=reservation_data.duration_minutes)
        end_time = reservation_data.start_time + duration_time

        if reservation_data.start_time < now():
            raise GraphQLError("Start time must be in the future.")

        if not pickup_branch or not return_branch:
            raise GraphQLError("Invalid branch.")

        required_transfer_time = Distance.objects.transfer_time(
            pickup_branch, return_branch
        )

        if required_transfer_time > duration_time:
            raise GraphQLError(
                f"Can't reach the branch: {return_branch} in time. Required transfer time: {total_minutes(required_transfer_time)} minutes."
            )

        car = find_available_car(
            reservation_data.start_time,
            end_time,
            pickup_branch,
            return_branch,
        )

        if not car:
            raise GraphQLError("No car available.")

        reservation = Reservation.objects.create(
            car=car,
            start_time=reservation_data.start_time,
            end_time=end_time,
            pickup_branch=pickup_branch,
            return_branch=return_branch,
        )

        return CreateReservation(ok=True, reservation=reservation)
        # return CreateReservation(reservation=reservation)


class Mutation(graphene.ObjectType):
    create_car = CreateCar.Field()
    delete_car = DeleteCar.Field()
    update_car = UpdateCar.Field()
    create_reservation = CreateReservation.Field()


class Query(graphene.ObjectType):
    all_cars = graphene.List(CarType)
    car = graphene.Field(CarType, car_id=graphene.String(required=True))
    upcoming_reservations = graphene.List(ReservationType)

    def resolve_all_cars(self, info, **kwargs):
        return Car.objects.all()

    def resolve_car(self, info, car_number):
        return Car.objects.get(car_number=car_number)

    def resolve_upcoming_reservations(self, info):
        return Reservation.objects.upcoming()


schema = graphene.Schema(query=Query, mutation=Mutation)
