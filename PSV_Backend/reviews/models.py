from django.db import models
from django.conf import settings
from decimal import Decimal


# Create your models here.

class PassengerReview(models.Model):
    """Review written by a passenger for a sacco or driver"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    sacco = models.ForeignKey("sacco.Sacco", on_delete=models.CASCADE, related_name="passenger_reviews")  
    cleanliness = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 11)])
    punctuality = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 11)])
    comfort = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 11)])
    overall = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)])
    average = models.DecimalField(max_digits=4, decimal_places=2, default=1.0)

    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.average = round(
            Decimal((self.cleanliness + self.punctuality + self.comfort + self.overall) / 4), 2
        )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"PassengerReview by {self.user.username} for {self.sacco.name} - Avg: {self.average}"

class OwnerReview(models.Model):
    """Vehicle owner reviews of a sacco"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    sacco = models.ForeignKey("sacco.Sacco", on_delete=models.CASCADE, related_name="owner_reviews")

    payment_punctuality = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 11)], help_text="How timely are payments?")
    driver_responsibility = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 11)], help_text="How careful are the drivers?")
    rate_fairness = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 11)], help_text="How fair are the charges?")
    support = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 11)], help_text="How responsive is the sacco management?")
    transparency = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 11)], help_text="How transparent is sacco decision-making?")
    overall = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 11)], help_text="Overall rating out of 5")

    average = models.DecimalField(max_digits=4, decimal_places=2, default=1.0)
    comment = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        score_total = (
            self.payment_punctuality +
            self.driver_responsibility +
            self.rate_fairness +
            self.support +
            self.transparency +
            self.overall
        )
        self.average = round(Decimal(score_total / 6), 2)
        super().save(*args, **kwargs)

    class Meta:
        unique_together = ('user', 'sacco')

    def __str__(self):
        return f"OwnerReview by {self.user.username} for {self.sacco.name} - Avg: {self.average}/10"
