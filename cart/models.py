from django.db import models
from django.conf import settings
from frontend.models import Products  # adjust if your product model is elsewhere

# Create your models here.
class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.username}'s Cart"

    def total_price(self):
        return sum(item.product.price for item in self.items.all())
        # return sum(item.total_price() for item in self.items.all())

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Products, on_delete=models.CASCADE)
    # quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.product.name}"
    
"""         def total_price(self):
        return self.product.price * self.quantity """



