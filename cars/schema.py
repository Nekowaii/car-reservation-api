import graphene
from graphene_django import DjangoObjectType
from django.utils.timezone import now
from cars.models import Branch, Car, Reservation
import datetime
from collections import defaultdict
from django.db.models import OuterRef, Subquery, Max, IntegerField, BigAutoField
from django.db.models.functions import Coalesce


class BranchType(DjangoObjectType):
    class Meta:
        model = Branch
        fields = (
            "id",
            "city",
        )


class BranchInput(graphene.InputObjectType):
    city = graphene.String(required=True)


class CarType(DjangoObjectType):
    status = graphene.String()
    current_branch = graphene.Field(BranchType)

    class Meta:
        model = Car
        fields = (
            "id",
            "car_number",
            "make",
            "model",
            "status",
            "branch",
            "current_branch",
        )

    def resolve_status(self, info):
        is_reserved = Reservation.objects.reserved_now().filter(car=self).exists()
        return "Unavailable" if is_reserved else "Available"

    def resolve_current_branch(self, info):
        last_reservation = (
            Reservation.objects.historical()
            .filter(car=self)
            .order_by("-end_time")
            .first()
        )

        if last_reservation:
            return last_reservation.return_branch

        return self.branch


class CarInput(graphene.InputObjectType):
    car_number = graphene.String(required=True)
    make = graphene.String(required=True)
    model = graphene.String(required=True)
    branch = BranchInput(required=True)


class CreateCar(graphene.Mutation):
    class Arguments:
        car_data = CarInput(required=True)

    # Output = CreateCarPayload
    car = graphene.Field(CarType)

    @staticmethod
    def mutate(root, info, car_data):
        branch = Branch.objects.get(city=car_data.branch.city)
        car = Car.objects.create(
            car_number=car_data.car_number,
            make=car_data.make,
            model=car_data.model,
            branch=branch,
        )
        return CreateCar(car=car)


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
        fields = (
            "id",
            "car",
            "start_time",
            "end_time",
            "pickup_branch",
            "return_branch",
        )


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

    @staticmethod
    def get_available_cars(start_time, duration_minutes, pickup_branch):
        end_time = start_time + datetime.timedelta(minutes=duration_minutes)
        reserved_between = Reservation.objects.reserved_between(start_time, end_time)
        available_cars = Car.objects.exclude(
            id__in=reserved_between.values_list("car_id", flat=True)
        )

        branch_to_cars = defaultdict(list)

        # for car in available_cars:
        print(available_cars)

        latest_reservations = (
            Reservation.objects.historical()
            .filter(car=OuterRef("pk"))
            .order_by("-end_time")
        )

        # print(latest_reservations.values("return_branch_id"))

        cars_with_latest_location = Car.objects.annotate(
            latest_location=Coalesce(
                Subquery(
                    latest_reservations.values("return_branch_id")[:1],
                    output_field=BigAutoField(),
                ),
                "branch_id",
            )
        )

        for car in cars_with_latest_location:
            print(car.id, car.make, car.model, car.latest_location)

    @classmethod
    def mutate(cls, root, info, reservation_data):
        pickup_branch = Branch.objects.get(city=reservation_data.pickup_branch.city)
        return_branch = Branch.objects.get(city=reservation_data.return_branch.city)
        cars = cls.get_available_cars(
            reservation_data.start_time,
            reservation_data.duration_minutes,
            pickup_branch,
        )
        return CreateReservation(ok=True)
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
        # current_time = now()
        # return Reservation.objects.filter(start_time__gt=current_time).order_by(
        #    "start_time"
        # )


schema = graphene.Schema(query=Query, mutation=Mutation)
