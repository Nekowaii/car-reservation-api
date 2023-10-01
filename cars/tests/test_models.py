from django.test import TestCase
from cars.models import Car, Branch, Distance, CarBranchLog, Reservation
from django.core.exceptions import ValidationError


# Create your tests here.
class CarTestCase(TestCase):
    def setUp(self):
        Car.objects.create(car_number="C123456789", make="Toyota", model="Camry")

    def test_car_number(self):
        message = "{'car_number': ['car_number must be in the format C<number>']}"
        with self.assertRaisesMessage(ValidationError, message):
            Car.objects.create(car_number="CBLABLABLA", make="Toyota", model="Camry")

    def test_uniq_car_number(self):
        message = "{'car_number': ['Car with this Car number already exists.']}"
        with self.assertRaisesMessage(ValidationError, message):
            Car.objects.create(car_number="C123456789", make="BMW", model="M3")

    def test_str(self):
        car = Car.objects.get(car_number="C123456789")
        self.assertEqual(str(car), "C123456789 Toyota Camry")


class BranchTestCase(TestCase):
    def setUp(self):
        Branch.objects.create(city="New York")

    def test_str(self):
        branch = Branch.objects.get(city="New York")
        self.assertEqual(str(branch), "New York")


class DistanceTestCase(TestCase):
    def setUp(self):
        new_york = Branch.objects.create(city="New York")
        boston = Branch.objects.create(city="Boston")
        Distance.objects.create(from_branch=new_york, to_branch=boston, distance_km=300)

    def test_from_to_branch_is_not_equal(self):
        boston = Branch.objects.create(city="Boston")
        message = "{'branch': ['Can not create distance between the same branch']}"
        with self.assertRaisesMessage(ValidationError, message):
            Distance.objects.create(
                from_branch=boston, to_branch=boston, distance_km=300
            )

    def test_str(self):
        distance = Distance.objects.get(distance_km=300)
        self.assertEqual(str(distance), "New York->Boston: 300km")


class ReservationTestCase(TestCase):
    def setUp(self):
        Branch.objects.create(city="New York")
        Car.objects.create(car_number="C123456789", make="Toyota", model="Camry")

    def test_car_branch_log_created(self):
        car = Car.objects.get(car_number="C123456789")
        branch = Branch.objects.get(city="New York")
        reservation = Reservation.objects.create(
            car=car,
            start_time="2020-01-01T00:00:00Z",
            end_time="2020-01-02T00:00:00Z",
            pickup_branch=branch,
            return_branch=branch,
        )
        car_branch_log = CarBranchLog.objects.filter(car=car)
        self.assertEqual(2, len(car_branch_log))
