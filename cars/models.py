from django.db import models
from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.utils.timezone import now
from cars.managers import (
    DistanceManager,
    CarManager,
    CarBranchLogManager,
    ReservationManager,
)


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


class Branch(models.Model):
    city = models.CharField(max_length=100, unique=True)

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

    objects = DistanceManager()

    def __str__(self):
        return f"{self.from_branch}->{self.to_branch}: {self.distance_km}km"

    def clean(self):
        if self.from_branch == self.to_branch:
            raise ValidationError(
                {"branch": ("Can not create distance between the same branch")}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super(Distance, self).save(*args, **kwargs)

    class Meta:
        unique_together = ("from_branch", "to_branch")


class CarBranchLog(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    timestamp = models.DateTimeField()

    objects = CarBranchLogManager()

    def __str__(self):
        return f"{self.car} {self.branch} {self.timestamp}"

    class Meta:
        unique_together = ("car", "branch", "timestamp")


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

    def save(self, *args, **kwargs):
        super(Reservation, self).save(*args, **kwargs)

        CarBranchLog.objects.create(
            car=self.car, branch=self.pickup_branch, timestamp=self.start_time
        )

        CarBranchLog.objects.create(
            car=self.car, branch=self.return_branch, timestamp=self.end_time
        )

    def __str__(self):
        return f"{self.car} {self.start_time} {self.end_time} {self.pickup_branch} {self.return_branch}"

    class Meta:
        unique_together = ("car", "start_time", "end_time")
