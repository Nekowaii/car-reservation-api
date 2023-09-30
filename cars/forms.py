from cars.models import Branch, Car, Reservation, CarBranchLog, Distance
from django.forms import ModelForm


# class ReservationForm(ModelForm):
#    class Meta:
#        model = Reservation
#
#        fields = (
#            "car",
#            "start_time",
#            "end_time",
#            "pickup_branch",
#            "return_branch",
#        )
#
#    def clean(self):
#        super(ReservationForm, self).clean()
#
#        start_time = self.cleaned_data.get("start_time")
#        start_time = cleaned_data.get("start_time")
#        end_time = cleaned_data.get("end_time")
#
#        # Check if start_time is greater than the current time
#        if start_time <= timezone.now():
#            raise ValidationError(
#                {"start_time": "Start time must be greater than the current time."}
#            )
#
#        # Check if start_time is less than end_time
#        if start_time >= end_time:
#            raise ValidationError(
#                {"end_time": "End time must be greater than start time."}
#            )
#
#        return cleaned_data
#
