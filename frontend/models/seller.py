# model/seller.py
from django.contrib.auth.models import User
from django.db import models
from django.utils.text import slugify

class Seller(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    store_name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True, null=True)
    owner_name = models.CharField(max_length=200, blank=True)

    logo = models.ImageField(
        upload_to="seller_logos/",
        blank=True,
        null=True
    )

    banner = models.ImageField(
        upload_to="seller_banners/",
        blank=True,
        null=True
    )

    email = models.EmailField(blank=True)

    phone = models.CharField(
        max_length=20,
        blank=True
    )

    whatsapp_number = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    address = models.TextField(blank=True)

    city = models.CharField(
        max_length=100,
        blank=True
    )

    state = models.CharField(
        max_length=100,
        blank=True
    )

    website = models.URLField(blank=True)

    description = models.TextField(blank=True)

    joined = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.store_name

    def save(self, *args, **kwargs):
      if not self.slug:
        self.slug = slugify(self.store_name)
        
      super().save(*args, **kwargs)
