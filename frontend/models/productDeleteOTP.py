from django.db import models
from .products import Products
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

class ProductDeleteOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Products, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=10)

    def __str__(self):
        return f"{self.user.username} OTP for {self.product.name}"

    class Meta:
        app_label = "frontend"
