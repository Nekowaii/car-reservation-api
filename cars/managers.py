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


class CarManager(models.Manager):
    def get_queryset(self):
        return CarQuerySet(self.model, using=self._db)

    def reserved_cars(self, start_time, end_time):
        return self.get_queryset().reserved_cars(start_time, end_time)

    def available_cars(self, start_time, end_time):
        reserved_cars = self.reserved_cars(start_time, end_time)
        return self.exclude(id__in=reserved_cars.values_list("id", flat=True))


class CarBranchLogQuerySet(models.QuerySet):
    def historical(self, end_time):
        return self.filter(timestamp__lt=end_time)

    def current_cars_branches(self, current_time):
        return self.filter(timestamp__lt=end_time).order_by("-timestamp")


class CarBranchLogManager(models.Manager):
    def get_queryset(self):
        return CarBranchLogQuerySet(self.model, using=self._db)

    def historical(self, end_time):
        return self.get_queryset().historical(end_time)


class ReservationQuerySet(models.QuerySet):
    def upcoming(self):
        return self.filter(start_time__gt=now()).order_by("start_time")

    def previous_reservations(self, date_time):
        return self.filter(end_time__lt=date_time).order_by("end_time")

    def next_reservations(self, date_time):
        return self.filter(start_time__gt=date_time).order_by("-start_time")

    def reserved_now(self, car):
        date_time = now()
        return self.filter(
            start_time__lte=date_time, end_time__gte=date_time, car=car
        ).order_by("start_time")

    def reserved_between(self, start_time, end_time):
        return self.filter(start_time__lte=end_time, end_time__gte=start_time)

    def historical(self):
        return self.filter(end_time__lt=now())


class ReservationManager(models.Manager):
    def get_queryset(self):
        return ReservationQuerySet(self.model, using=self._db)

    def upcoming(self):
        return self.get_queryset().upcoming()

    def previous_reservations(self, date_time):
        return self.get_queryset().previous_reservations(date_time)

    def next_reservations(self, date_time):
        return self.get_queryset().next_reservations(date_time)

    def reserved_between(self, start_time, end_time):
        return self.get_queryset().reserved_between(start_time, end_time)

    def historical(self):
        return self.get_queryset().historical()

    def reserved_now(self, car):
        return self.get_queryset().reserved_now(car)
