from django.db import models
from frontend.storage import ProductMediaCloudinaryStorage


class Material(models.Model):

    MATERIAL_TYPES = (
        ("thread", "Thread"),
        ("wool", "Wool"),
        ("yarn", "Yarn"),
        ("other", "Other"),
    )

    name = models.CharField(
        max_length=100,
        unique=True
    )

    material_type = models.CharField(
        max_length=20,
        choices=MATERIAL_TYPES,
        default="other"
    )

    description = models.TextField(
        blank=True
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.name


class MaterialVariant(models.Model):

    material = models.ForeignKey(
        Material,
        on_delete=models.CASCADE,
        related_name="variants"
    )

    name = models.CharField(
        max_length=100
    )

    specification = models.CharField(
        max_length=255,
        blank=True
    )

    is_active = models.BooleanField(
        default=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["material", "name"],
                name="unique_material_variant"
            )
        ]

    def __str__(self):
        return f"{self.material.name} - {self.name}"


class MaterialColor(models.Model):

    material_variant = models.ForeignKey(
        MaterialVariant,
        on_delete=models.CASCADE,
        related_name="colors"
    )

    name = models.CharField(
        max_length=100
    )

    color_code = models.CharField(
        max_length=20,
        blank=True
    )

    hex_code = models.CharField(
        max_length=7,
        blank=True
    )

    is_active = models.BooleanField(
        default=True
    )

    def __str__(self):
        return (
            f"{self.material_variant.material.name} - "
            f"{self.material_variant.name} - "
            f"{self.name}"
        )


class MaterialColorImage(models.Model):

    material_color = models.ForeignKey(
        MaterialColor,
        on_delete=models.CASCADE,
        related_name="images"
    )

    image = models.ImageField(
        upload_to="uploads/materials/colors/",
        # storage=ProductMediaCloudinaryStorage(),
    )

    alt_text = models.CharField(
        max_length=255,
        blank=True
    )

    is_primary = models.BooleanField(
        default=False
    )

    order = models.PositiveIntegerField(
        default=0
    )

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.material_color} - Image"


class MaterialInventory(models.Model):

    material_color = models.OneToOneField(
        MaterialColor,
        on_delete=models.CASCADE,
        related_name="inventory"
    )

    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    unit = models.CharField(
        max_length=20,
        default="unit"
    )

    is_available = models.BooleanField(
        default=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return (
            f"{self.material_color}: "
            f"{self.quantity} {self.unit}"
        )