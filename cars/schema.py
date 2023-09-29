import graphene
from graphene_django import DjangoObjectType

from cars.models import Branch, Car, Reservation


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
    class Meta:
        model = Car
        fields = (
            "id",
            "car_number",
            "make",
            "model",
            "branch",
        )


class CarInput(graphene.InputObjectType):
    car_number = graphene.String(required=True)
    make = graphene.String(required=True)
    model = graphene.String(required=True)
    branch = BranchInput(required=True)


# class CreateCarPayload(graphene.ObjectType):
#    car = graphene.Field(CarType, required=True)


class CreateCar(graphene.Mutation):
    class Arguments:
        # car_data = CarInput(required=True, name="input")
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
        # return CreateCarPayload(car=car)
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

    # Output = CreateCarPayload
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


class Mutation(graphene.ObjectType):
    create_car = CreateCar.Field()
    delete_car = DeleteCar.Field()
    update_car = UpdateCar.Field()


class Query(graphene.ObjectType):
    all_cars = graphene.List(CarType)
    car = graphene.Field(CarType, car_id=graphene.String(required=True))

    def resolve_all_cars(self, info, **kwargs):
        return Car.objects.select_related("branch").all()
        # return Car.objects.select_related("branch").all()

    def resolve_car(self, info, car_number):
        return Car.objects.get(car_number=car_number)


schema = graphene.Schema(query=Query, mutation=Mutation)
