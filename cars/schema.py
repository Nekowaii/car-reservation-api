import graphene
from graphene_django import DjangoObjectType
from django.utils.timezone import now
from cars.models import Branch, Car, Reservation, CarBranchLog, Distance
import datetime
from collections import defaultdict
from django.db.models import OuterRef, Subquery, Max, IntegerField, BigAutoField
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
        fields = ["id", "car_number", "make", "model", "current_branch"]

    def resolve_current_branch(self, info):
        return (
            CarBranchLog.objects.historical(from_time=now())
            .filter(car=self)
            .first()
            .branch
        )


class CarInput(graphene.InputObjectType):
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
        car_data = CarInput(required=True)

    # Output = CreateCarPayload
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
        car.delete()
        return DeleteCar(ok=True)


class UpdateCar(graphene.Mutation):
    class Arguments:
        car_data = CarInput(required=True)

    car = graphene.Field(CarType)

    @staticmethod
    def mutate(root, info, car_data):
        car = Car.objects.get(car_number=car_data.car_number)
        car.make = car_data.make
        car.model = car_data.model
        car.branch = Branch.objects.get(city=car_data.branch.city)
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

    @staticmethod
    def find_available_car(start_time, end_time, pickup_branch, return_branch):
        branch_to_cars = defaultdict(list)
        # end_time = start_time + datetime.timedelta(minutes=duration_minutes)

        # available_cars = Car.objects.available_at_branch_between(
        #    start_time, end_time, pickup_branch
        # )

        available_cars = Car.objects.available_between(start_time, end_time)

        latest_car_branch = (
            CarBranchLog.objects.filter(timestamp__lt=start_time, car=OuterRef("pk"))
            .order_by("-timestamp")
            .values("branch_id")[:1]
        )

        available_cars = available_cars.annotate(
            current_branch_id=Subquery(latest_car_branch)
        )

        next_reservations = {
            res.car_id: res
            for res in Reservation.objects.next_reservations(end_time).filter(
                car__in=available_cars
            )
        }

        previous_reservations = {
            res.car_id: res
            for res in Reservation.objects.previous_reservations(start_time).filter(
                car__in=available_cars
            )
        }

        for car in available_cars:
            branch_to_cars[car.current_branch_id].append(car)

        def is_car_available_next(res, end_time, return_branch):
            if res.pickup_branch == return_branch and res.start_time > end_time:
                return True

            required_transfer_time = Distance.objects.transfer_time(
                res.pickup_branch, return_branch
            )

            if required_transfer_time:
                if end_time + required_transfer_time <= res.start_time:
                    return True

            return False

        print(branch_to_cars)
        print(next_reservations)
        print("SEARCHING IN THE CURRENT BRANCH...")
        for car in branch_to_cars[pickup_branch.id]:
            res = next_reservations.get(car.id, None)
            if not res or is_car_available_next(res, end_time, return_branch):
                print(car)
                return car

        print("NO CAR AVAILABLE AT CURRENT BRANCH")
        print("SEARCHING IN OTHER BRANCHES...")

        def is_car_available_prev(res, start_time, pickup_branch):
            if res.return_branch == pickup_branch and res.end_time < start_time:
                return True

            required_transfer_time = Distance.objects.transfer_time(
                res.return_branch, pickup_branch
            )

            if required_transfer_time:
                if start_time - required_transfer_time >= res.end_time:
                    return True

            return False

        for branch_id, cars in branch_to_cars.items():
            if branch_id == pickup_branch.id:
                continue
            print(pickup_branch.id, start_time, branch_id, cars)
            for car in cars:
                res = next_reservations.get(car.id, None)
                if res and not is_car_available_next(res, end_time, return_branch):
                    continue
                res = previous_reservations.get(car.id, None)
                if res and not is_car_available_prev(res, end_time, return_branch):
                    continue
                print(car, car.current_branch_id)
                return car

        return None

    @classmethod
    def mutate(cls, root, info, reservation_data):
        pickup_branch = Branch.objects.get(city=reservation_data.pickup_branch.city)
        return_branch = Branch.objects.get(city=reservation_data.return_branch.city)
        end_time = reservation_data.start_time + datetime.timedelta(
            minutes=reservation_data.duration_minutes
        )

        car = cls.find_available_car(
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
        CarBranchLog.objects.create(
            car=car, branch=pickup_branch, timestamp=reservation.start_time
        )
        CarBranchLog.objects.create(
            car=car, branch=return_branch, timestamp=reservation.end_time
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
