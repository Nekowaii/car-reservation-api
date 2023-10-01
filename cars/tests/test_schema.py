import json

from graphene_django.utils.testing import GraphQLTestCase
from django.utils.timezone import now
from datetime import timedelta
from cars.models import Car, Branch, Distance, CarBranchLog, Reservation
from django.test import TestCase
from graphql import GraphQLError
from django.core.exceptions import ValidationError


def load_sample_data():
    # branches
    branch_1 = Branch.objects.create(city="Boston")
    branch_2 = Branch.objects.create(city="New York")
    branch_3 = Branch.objects.create(city="Chicago")

    # cars
    car = Car.objects.create(car_number="C123456789", make="Toyota", model="Camry")
    # car branch logs
    CarBranchLog.objects.create(
        car=car,
        branch=Branch.objects.get(city="Boston"),
        timestamp=now() - timedelta(days=1),
    )

    # distances
    Distance.objects.create(from_branch=branch_1, to_branch=branch_2, distance_km=300)
    Distance.objects.create(from_branch=branch_2, to_branch=branch_1, distance_km=300)
    Distance.objects.create(from_branch=branch_1, to_branch=branch_3, distance_km=1000)
    Distance.objects.create(from_branch=branch_3, to_branch=branch_1, distance_km=1000)
    Distance.objects.create(from_branch=branch_2, to_branch=branch_3, distance_km=800)
    Distance.objects.create(from_branch=branch_3, to_branch=branch_2, distance_km=800)

    # reservations
    historical_reservation = Reservation.objects.create(
        car=car,
        pickup_branch=branch_1,
        return_branch=branch_2,
        start_time=now() - timedelta(days=2),
        end_time=now() - timedelta(days=1),
    )
    upcoming_reservation = Reservation.objects.create(
        car=car,
        pickup_branch=branch_1,
        return_branch=branch_2,
        start_time=now() + timedelta(days=1),
        end_time=now() + timedelta(days=2),
    )

    return historical_reservation, upcoming_reservation


class QueryTestCase(GraphQLTestCase):
    def setUp(self):
        self.historical_reservation, self.upcoming_reservation = load_sample_data()

    def test_query_car(self):
        response = self.query(
            """
            query {
                allCars {
                    id
                    carNumber
                    make
                    model
                }
            }
            """
        )
        content = json.loads(response.content)

        self.assertResponseNoErrors(response)

        expected_content = {
            "data": {
                "allCars": [
                    {
                        "id": "1",
                        "carNumber": "C123456789",
                        "make": "Toyota",
                        "model": "Camry",
                    }
                ]
            }
        }

        self.assertEqual(
            content["data"]["allCars"][0], expected_content["data"]["allCars"][0]
        )

    def test_quert_upcoming_reservations(self):
        response = self.query(
            """
            query {
                upcomingReservations {
                    id
                    car {
                        id
                        carNumber
                        make
                        model
                    }
                    pickupBranch {
                        id
                        city
                    }
                    returnBranch {
                        id
                        city
                    }
                }
            }
            """
        )
        content = json.loads(response.content)

        self.assertResponseNoErrors(response)

        r = self.upcoming_reservation
        expected_content = {
            "data": {
                "upcomingReservations": [
                    {
                        "id": str(r.id),
                        "car": {
                            "id": str(r.car.id),
                            "carNumber": r.car.car_number,
                            "make": r.car.make,
                            "model": r.car.model,
                        },
                        "pickupBranch": {
                            "id": str(r.pickup_branch.id),
                            "city": r.pickup_branch.city,
                        },
                        "returnBranch": {
                            "id": str(r.return_branch.id),
                            "city": r.return_branch.city,
                        },
                    }
                ]
            }
        }

        self.assertEqual(
            content["data"]["upcomingReservations"][0],
            expected_content["data"]["upcomingReservations"][0],
        )


class MutationTestCase(GraphQLTestCase):
    def setUp(self):
        self.historical_reservation, self.upcoming_reservation = load_sample_data()

    def test_create_car(self):
        response = self.query(
            """
            mutation {
                createCar(carData: {carNumber: "C523671934", make: "BMW", model: "X7", branch: {city: "Boston"}}) {
                    car {
                        carNumber,
                        make,
                        model
                    }
                }
            }
            """
        )

        content = json.loads(response.content)

        self.assertResponseNoErrors(response)

        expected_content = {
            "data": {
                "createCar": {
                    "car": {"carNumber": "C523671934", "make": "BMW", "model": "X7"}
                }
            }
        }

        self.assertEqual(
            content["data"]["createCar"]["car"],
            expected_content["data"]["createCar"]["car"],
        )

    def test_update_car(self):
        response = self.query(
            """
            mutation {
                updateCar(carData: {carNumber: "C123456789", make: "Toyota", model: "Camry New"}) {
                    car {
                        carNumber,
                        make,
                        model
                    }
                }
            }
            """
        )

        content = json.loads(response.content)

        self.assertResponseNoErrors(response)

        expected_content = {
            "data": {
                "updateCar": {
                    "car": {
                        "carNumber": "C123456789",
                        "make": "Toyota",
                        "model": "Camry New",
                    }
                }
            }
        }

        self.assertEqual(
            content["data"]["updateCar"]["car"],
            expected_content["data"]["updateCar"]["car"],
        )

    def test_delete_car(self):
        response = self.query(
            """
            mutation {
                deleteCar(carNumber: "C123456789") {
                    ok
                }
            }
            """
        )

        content = json.loads(response.content)

        self.assertResponseNoErrors(response)

        expected_content = {"data": {"deleteCar": {"ok": True}}}

        self.assertEqual(
            content["data"]["deleteCar"]["ok"],
            expected_content["data"]["deleteCar"]["ok"],
        )

    def test_create_reservation_no_bounds(self):
        current_time = now()
        start_time = now() + timedelta(minutes=10)
        end_time = start_time + timedelta(minutes=400)

        start_time = start_time.strftime("%Y-%m-%dT%H:%M:%S+00:00")
        end_time = end_time.strftime("%Y-%m-%dT%H:%M:%S+00:00")

        response = self.query(
            """
            mutation {
                createReservation(reservationData: {pickupBranch: {city: "Boston"}, returnBranch: {city: "New York"}, startTime: \""""
            + start_time
            + """\", durationMinutes: 400}) {
                    reservation {
                        id
                        car {
                            id
                            carNumber
                            make
                            model
                        }
                        pickupBranch {
                            id
                            city
                        }
                        returnBranch {
                            id
                            city
                        }
                        startTime
                        endTime
                    }
                }
            }
            """
        )

        content = json.loads(response.content)

        self.assertResponseNoErrors(response)

        expected_content = {
            "data": {
                "createReservation": {
                    "reservation": {
                        "id": "3",
                        "car": {
                            "id": "1",
                            "carNumber": "C123456789",
                            "make": "Toyota",
                            "model": "Camry",
                        },
                        "pickupBranch": {"id": "1", "city": "Boston"},
                        "returnBranch": {"id": "2", "city": "New York"},
                        "startTime": start_time,
                        "endTime": end_time,
                    }
                }
            }
        }

        self.assertEqual(
            content["data"]["createReservation"]["reservation"],
            expected_content["data"]["createReservation"]["reservation"],
        )

    def test_create_reservation_bounds(self):
        start_time = now() + timedelta(hours=10)
        end_time = start_time + timedelta(minutes=3000)

        start_time = start_time.strftime("%Y-%m-%dT%H:%M:%S+00:00")
        end_time = end_time.strftime("%Y-%m-%dT%H:%M:%S+00:00")

        with self.assertRaises(AssertionError):
            response = self.query(
                """
            mutation {
                createReservation(reservationData: {pickupBranch: {city: "Boston"}, returnBranch: {city: "New York"}, startTime: \""""
                + start_time
                + """\", durationMinutes: 3000}) {
                    reservation {
                        id
                        car {
                            id
                            carNumber
                            make
                            model
                        }
                        pickupBranch {
                            id
                            city
                        }
                        returnBranch {
                            id
                            city
                        }
                        startTime
                        endTime
                    }
                }
            }
            """
            )
            self.assertResponseNoErrors(response)
