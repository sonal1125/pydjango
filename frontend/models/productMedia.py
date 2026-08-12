from django.db import models
from .products import Products
from frontend.storage import ProductMediaCloudinaryStorage

class ProductMedia(models.Model):
    product = models.ForeignKey(
        Products,
        on_delete=models.CASCADE,
        related_name="media"
    )

    # file = models.FileField(upload_to="uploads/products/")
    file = models.FileField(
        upload_to="uploads/products/",
        storage=ProductMediaCloudinaryStorage(),
        )
    MEDIA_CHOICES = (
        ("image", "Image"),
        ("video", "Video"),
    )

    media_type = models.CharField(
        max_length=10,
        choices=MEDIA_CHOICES,
        default="image",
    )

    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    alt_text = models.CharField(
        max_length=255,
        blank=True,
    )

    def __str__(self):
        return f"{self.product.name} - {self.media_type}"