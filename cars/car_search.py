from collections import defaultdict
from cars.models import Car, Distance, CarBranchLog, Reservation
from django.db.models import OuterRef, Subquery


def find_available_car(start_time, end_time, pickup_branch, return_branch):
    branch_to_cars = defaultdict(list)
    latest_car_branch = (
        CarBranchLog.objects.filter(timestamp__lt=start_time, car=OuterRef("pk"))
        .order_by("-timestamp")
        .values("branch_id")[:1]
    )
    available_cars = Car.objects.available_cars(start_time, end_time).annotate(
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
