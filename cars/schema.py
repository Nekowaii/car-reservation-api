import graphene
from graphene_django import DjangoObjectType
from django.utils.timezone import now
from cars.models import Branch, Car, Reservation, CarBranchLog, Distance
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
    current_branch = graphene.Field(BranchType)

    class Meta:
        model = Car
        fields = (
            "id",
            "car_number",
            "make",
            "model",
            "current_branch",
        )

    def resolve_current_branch(self, info):
        return CarBranchLog.objects.historical().filter(car=self).first().branch


class CarInput(graphene.InputObjectType):
    car_number = graphene.String(required=True)
    make = graphene.String(required=True)
    model = graphene.String(required=True)
    branch = BranchInput(required=True)


class CarBranchLogType(DjangoObjectType):
    class Meta:
        model = CarBranchLog
        fields = (
            "id",
            "car",
            "branch",
            "timestamp",
        )


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
    def get_available_car(start_time, duration_minutes, pickup_branch, return_branch):
        branch_to_cars = defaultdict(list)
        end_time = start_time + datetime.timedelta(minutes=duration_minutes)

        latest_car_branch = (
            CarBranchLog.objects.historical()
            .filter(car=OuterRef("pk"))
            .order_by("-timestamp")
            .values("branch_id")[:1]
        )

        available_cars = Car.objects.available_between(start_time, end_time).annotate(
            current_branch_id=Subquery(latest_car_branch),
        )

        def is_car_available(start_time, end_time, pickup_branch, return_branch):
            transfer_time = transfer_time(pickup_branch, return_branch)

            print(Reservation.objects.reserved_at(start_time - transfer_time))

            if Reservation.objects.reserved_at(
                start_time - transfer_time
            ) or Reservation.objects.reserved_at(start_time - transfer_time):
                return False

            if not transfer_time:
                return False

            return end_time + transfer_time < now()

        for car in available_cars:
            print(car.current_branch_id)
            if car.current_branch_id != pickup_branch.id:
                required_transfer_time = Distance.objects.transfer_time(
                    car.current_branch_id, pickup_branch.id
                )

                if (
                    not required_transfer_time
                    or start_time - required_transfer_time < now()
                    and Reservation.objects.reserved_at(
                        start_time - required_transfer_time
                    )
                ):
                    # skip
                    continue

            if car.current_branch_id != return_branch.id:
                required_transfer_time = Distance.objects.transfer_time(
                    car.current_branch_id, return_branch.id
                )

                if not required_transfer_time or Reservation.objects.reserved_at(
                    end_time + required_transfer_time
                ):
                    # skip
                    continue

            #    print(pickup_branch, car.current_branch_id)
            #    distance = Distance.objects.get(
            #        from_branch=pickup_branch, to_branch=car.current_branch_id
            #    )
            #    print(distance.distance_km)

            # Distance.objects.get(
            #    from_branch=pickup_branch, to_branch=car.current_branch_id
            # )
            # car.current_branch_id
            # branch_to_cars[car.current_branch_id].append(car)

        # if branch_to_cars[pickup_branch.id]:
        #    car = branch_to_cars[pickup_branch.id][0]
        #    return car

        return available_cars

    @classmethod
    def mutate(cls, root, info, reservation_data):
        pickup_branch = Branch.objects.get(city=reservation_data.pickup_branch.city)
        return_branch = Branch.objects.get(city=reservation_data.return_branch.city)
        car = cls.get_available_car(
            reservation_data.start_time,
            reservation_data.duration_minutes,
            pickup_branch,
            return_branch,
        )
        # Reservation.objects.create()
        return CreateReservation(ok=True)
        # return CreateReservation(reservation=reservation)


class Mutation(graphene.ObjectType):
    create_car = CreateCar.Field()
    delete_car = DeleteCar.Field()
    update_car = UpdateCar.Field()
    create_reservation = CreateReservation.Field()


class Query(graphene.ObjectType):
    all_cars = graphene.List(CarType)
    # car = graphene.Field(CarType, car_id=graphene.String(required=True))
    # upcoming_reservations = graphene.List(ReservationType)

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
