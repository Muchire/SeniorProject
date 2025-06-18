from django import forms
from .models import PassengerReview, OwnerReview

class PassengerReviewForm(forms.ModelForm):
    """Form for passengers to review a sacco"""

    class Meta:
        model = PassengerReview
        fields = [
            'cleanliness',
            'punctuality',
            'comfort',
            'overall',
            'comment',
        ]
        widgets = {
            'cleanliness': forms.RadioSelect(),
            'punctuality': forms.RadioSelect(),
            'comfort': forms.RadioSelect(),
            'overall': forms.RadioSelect(),
            'comment': forms.Textarea(
                attrs={'rows': 4, 'placeholder': 'Share your experience as a passenger.'}
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        for field in ['cleanliness', 'punctuality', 'comfort']:
            value = cleaned_data.get(field)
            if not 1 <= value <= 10:
                self.add_error(field, 'Rating must be between 1 and 10.')
        return cleaned_data


class OwnerReviewForm(forms.ModelForm):
    """Form for vehicle owners to review a sacco"""

    class Meta:
        model = OwnerReview
        fields = [
            'payment_punctuality',
            'driver_responsibility',
            'rate_fairness',
            'support',
            'transparency',
            'overall',
            'comment',
        ]
        widgets = {
            'payment_punctuality': forms.RadioSelect(),
            'driver_responsibility': forms.RadioSelect(),
            'rate_fairness': forms.RadioSelect(),
            'support': forms.RadioSelect(),
            'transparency': forms.RadioSelect(),
            'overall': forms.RadioSelect(),
            'comment': forms.Textarea(
                attrs={'rows': 4, 'placeholder': 'Share your experience as a vehicle owner.'}
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        for field in ['payment_punctuality', 'driver_responsibility', 'rate_fairness', 'support', 'transparency']:
            value = cleaned_data.get(field)
            if not 1 <= value <= 10:
                self.add_error(field, 'Rating must be between 1 and 10.')
        return cleaned_data
