from django.db import models
from django.utils.timezone import now
import datetime


class DistanceQuerySet(models.QuerySet):
    def distance(self, from_branch, to_branch):
        return self.filter(from_branch=from_branch, to_branch=to_branch).first()


class DistanceManager(models.Manager):
    CAR_SPEED = 80

    def get_queryset(self):
        return DistanceQuerySet(self.model, using=self._db)

    def distance_km(self, from_branch, to_branch):
        if from_branch == to_branch:
            return 0

        distance = self.get_queryset().distance(from_branch, to_branch)

        if not distance:
            return None

        return distance.distance_km

    def transfer_time(self, from_branch, to_branch):
        distance = self.get_queryset().distance(from_branch, to_branch)
        if not distance:
            return None

        return datetime.timedelta(hours=distance.distance_km / self.CAR_SPEED)


class CarQuerySet(models.QuerySet):
    def reserved_cars(self, start_time, end_time):
        return self.filter(
            reservation__start_time__lte=end_time,
            reservation__end_time__gte=start_time,
        )

    def with_current_branch(self, current_time):
        latest_car_branch = (
            self.filter(
                carbranchlog__timestamp__lt=current_time,
                carbranchlog__car=models.OuterRef("pk"),
            )
            .order_by("-carbranchlog__timestamp")
            .values("carbranchlog__branch_id")[:1]
        )
        return self.annotate(current_branch_id=models.Subquery(latest_car_branch))


class CarManager(models.Manager):
    def get_queryset(self):
        return CarQuerySet(self.model, using=self._db)

    def reserved_cars(self, start_time, end_time):
        return self.get_queryset().reserved_cars(start_time, end_time)

    def available_cars(self, start_time, end_time, include_branch=True):
        reserved_cars = self.reserved_cars(start_time, end_time)
        return self.exclude(id__in=reserved_cars.values_list("id", flat=True))


class ReservationQuerySet(models.QuerySet):
    def upcoming(self):
        return self.filter(start_time__gt=now()).order_by("start_time")

    # def previous_reservations(self, date_time):
    #    return self.filter(end_time__lt=date_time).order_by("end_time")

    # def next_reservations(self, date_time):
    #    return self.filter(start_time__gt=date_time).order_by("-start_time")

    def next_reservations(self, date_time):
        next_reservation = self.filter(
            start_time__gt=date_time, car_id=models.OuterRef("car_id")
        ).order_by("start_time")[:1]

        return self.filter(id__in=models.Subquery(next_reservation.values("id")))

    def previous_reservations(self, date_time):
        previous_reservation = self.filter(
            end_time__lt=date_time, car_id=models.OuterRef("car_id")
        ).order_by("-end_time")[:1]

        return self.filter(id__in=models.Subquery(previous_reservation.values("id")))

    def reserved_now(self, car):
        date_time = now()
        return self.filter(
            start_time__lte=date_time, end_time__gte=date_time, car=car
        ).order_by("start_time")


class ReservationManager(models.Manager):
    def get_queryset(self):
        return ReservationQuerySet(self.model, using=self._db)

    def upcoming(self):
        return self.get_queryset().upcoming()

    # def previous_reservations(self, date_time):
    #    return self.get_queryset().previous_reservations(date_time)

    # def next_reservations(self, date_time):
    #    return self.get_queryset().next_reservations(date_time)

    def reserved_now(self, car):
        return self.get_queryset().reserved_now(car)

    def next_reservations(self, date_time):
        return self.get_queryset().next_reservations(date_time)

    def previous_reservations(self, date_time):
        return self.get_queryset().previous_reservations(date_time)
