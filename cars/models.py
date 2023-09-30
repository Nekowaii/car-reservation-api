from django.db import models
from django.core.validators import RegexValidator
from django.utils.timezone import now
import datetime


class CarNumberField(models.CharField):
    default_validators = [
        RegexValidator(
            regex="^C[0-9]+$",
            message="car_number must be in the format C<number>",
            code="invalid_car_number",
        )
    ]
    description = "Car Number"

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("max_length", 254)
        super().__init__(*args, **kwargs)


class Branch(models.Model):
    city = models.CharField(max_length=100)

    def __str__(self):
        return self.city


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


class Distance(models.Model):
    from_branch = models.ForeignKey(
        Branch, on_delete=models.CASCADE, related_name="from_branch"
    )
    to_branch = models.ForeignKey(
        Branch, on_delete=models.CASCADE, related_name="to_branch"
    )
    distance_km = models.PositiveIntegerField()

    objects = DistanceManager()

    def __str__(self):
        return f"{self.from_branch} {self.to_branch} {self.distance_km}"


class CarQuerySet(models.QuerySet):
    def available_between(self, start_time, end_time):
        reserved_car_ids = Reservation.objects.reserved_between(
            start_time, end_time
        ).values_list("car_id", flat=True)
        return self.exclude(id__in=reserved_car_ids)


class CarManager(models.Manager):
    def get_queryset(self):
        return CarQuerySet(self.model, using=self._db)

    def available_between(self, start_time, end_time):
        return self.get_queryset().available_between(start_time, end_time)


class Car(models.Model):
    id = models.BigAutoField(primary_key=True)
    car_number = CarNumberField(unique=True)
    make = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    objects = CarManager()

    def __str__(self):
        return f"{self.car_number} {self.make} {self.model}"

    def save(self, *args, **kwargs):
        self.full_clean()
        super(Car, self).save(*args, **kwargs)


class CarBranchQuerySet(models.QuerySet):
    def historical(self):
        return self.filter(timestamp__lt=now())

    def historical_branch(self, branch):
        return self.historical().filter(branch=branch)


class CarBranchLogManager(models.Manager):
    def get_queryset(self):
        return CarBranchQuerySet(self.model, using=self._db)

    def historical(self):
        return self.get_queryset().historical().order_by("timestamp")

    def historical_branch(self, branch):
        return self.get_queryset().historical_branch(branch).order_by("timestamp")


class CarBranchLog(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    timestamp = models.DateTimeField()

    objects = CarBranchLogManager()

    def __str__(self):
        return f"{self.car} {self.branch} {self.timestamp}"


class ReservationQuerySet(models.QuerySet):
    def upcoming(self):
        return self.filter(start_time__gt=now()).order_by("start_time")

    def reserved_at(self, date_time):
        return self.filter(start_time__lte=date_time, end_time__gte=date_time).order_by(
            "start_time"
        )

    def reserved_between(self, start_time, end_time):
        return self.filter(start_time__lte=end_time, end_time__gte=start_time)

    def historical(self):
        return self.filter(end_time__lt=now())


class ReservationManager(models.Manager):
    def get_queryset(self):
        return ReservationQuerySet(self.model, using=self._db)

    def upcoming(self):
        return self.get_queryset().upcoming()

    def reserved_at(self, date_time):
        return self.get_queryset().reserved_at(date_time)

    def reserved_between(self, start_time, end_time):
        return self.get_queryset().reserved_between(start_time, end_time)

    def historical(self):
        return self.get_queryset().historical()


class Reservation(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    pickup_branch = models.ForeignKey(
        Branch, on_delete=models.CASCADE, related_name="pickup_branch"
    )
    return_branch = models.ForeignKey(
        Branch, on_delete=models.CASCADE, related_name="return_branch"
    )

    objects = ReservationManager()

    def __str__(self):
        return f"{self.car} {self.start_time} {self.end_time} {self.pickup_branch} {self.return_branch}"
