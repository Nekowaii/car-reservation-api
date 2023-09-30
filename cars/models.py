from django.db import models
from django.core.validators import RegexValidator
from django.utils.timezone import now


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


class Distance(models.Model):
    from_branch = models.ForeignKey(
        Branch, on_delete=models.CASCADE, related_name="from_branch"
    )
    to_branch = models.ForeignKey(
        Branch, on_delete=models.CASCADE, related_name="to_branch"
    )
    distance_km = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.from_branch} {self.to_branch} {self.distance_km}"


class Car(models.Model):
    # class Status(models.IntegerChoices):
    #    AVAILABLE = 1
    #    RESERVED = 2
    #    IN_TRANSIT = 3
    #    TO_BE_DELETED = 4
    #    TO_BE_UPDATED = 5

    id = models.BigAutoField(primary_key=True)
    car_number = CarNumberField(unique=True)
    make = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    # status = models.PositiveSmallIntegerField(
    #    choices=Status.choices, default=Status.AVAILABLE
    # )

    def __str__(self):
        return f"{self.car_number} {self.make} {self.model}"

    def save(self, *args, **kwargs):
        self.full_clean()
        super(Car, self).save(*args, **kwargs)


class ReservationQuerySet(models.QuerySet):
    def upcoming(self):
        return self.filter(start_time__gt=now()).order_by("start_time")

    def reserved_now(self):
        current_time = now()
        return self.filter(
            start_time__lte=current_time, end_time__gte=current_time
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

    def reserved_now(self):
        return self.get_queryset().reserved_now()

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
