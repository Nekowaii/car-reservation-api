from collections import defaultdict
from cars.models import Car, Distance, Reservation, Branch
from graphql import GraphQLError
from django.db import transaction


def is_car_available_lower_bound(res, start_time, pickup_branch):
    if res.return_branch == pickup_branch and res.end_time < start_time:
        return True
    required_transfer_time = Distance.objects.transfer_time(
        res.return_branch, pickup_branch
    )
    if required_transfer_time:
        if start_time - required_transfer_time >= res.end_time:
            return True
    return False


def is_car_available_upper_bound(res, end_time, return_branch):
    if res.pickup_branch == return_branch and res.start_time > end_time:
        return True
    required_transfer_time = Distance.objects.transfer_time(
        res.pickup_branch, return_branch
    )
    if required_transfer_time:
        if end_time + required_transfer_time <= res.start_time:
            return True
    return False


def get_available_cars(start_time, end_time, pickup_branch, return_branch):
    branch_to_cars = defaultdict(list)
    available_cars = Car.objects.available_cars(
        start_time, end_time
    ).with_current_branch(start_time)

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

    # print("SEARCHING IN THE CURRENT BRANCH...")
    for car in branch_to_cars[pickup_branch.id]:
        res = next_reservations.get(car.id, None)
        if not res or is_car_available_upper_bound(res, end_time, return_branch):
            yield car
    # print("NO CAR AVAILABLE AT CURRENT BRANCH")
    # print("SEARCHING IN OTHER BRANCHES...")

    for branch_id, cars in branch_to_cars.items():
        if branch_id == pickup_branch.id:
            continue

        for car in cars:
            res = next_reservations.get(car.id, None)
            if res and not is_car_available_upper_bound(res, end_time, return_branch):
                continue
            res = previous_reservations.get(car.id, None)
            if res and not is_car_available_lower_bound(res, start_time, pickup_branch):
                continue
            yield car


def reserve_car(start_time, end_time, pickup_branch, return_branch):
    cars = get_available_cars(start_time, end_time, pickup_branch, return_branch)
    car = next(cars, None)

    if not car:
        return None

    return Reservation.objects.create(
        car=car,
        start_time=start_time,
        end_time=end_time,
        pickup_branch=pickup_branch,
        return_branch=return_branch,
    )


def get_nearest_car(pickup_branch, cars):
    nearest_car = None
    nearest_distance = float("inf")

    for car in cars:
        car_branch = Branch.objects.get(id=car.current_branch_id)
        distance = Distance.objects.distance_km(
            from_branch=car_branch, to_branch=pickup_branch
        )

        if distance is None:
            raise GraphQLError("No distance between the branches.")

        if distance < nearest_distance:
            nearest_distance = distance
            nearest_car = car

    return nearest_car


@transaction.atomic
def reserve_cars(reservation_request_list):
    reservations = []
    reservation_request_list.sort(key=lambda x: x[0])

    for reservation_request in reservation_request_list:
        start_time, end_time, pickup_branch, return_branch = reservation_request

        cars = list(
            get_available_cars(start_time, end_time, pickup_branch, return_branch)
        )

        if not cars:
            return []

        car = get_nearest_car(pickup_branch, cars)

        reservation = Reservation.objects.create(
            car=car,
            start_time=start_time,
            end_time=end_time,
            pickup_branch=pickup_branch,
            return_branch=return_branch,
        )
        reservations.append(reservation)

    return reservations
