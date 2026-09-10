# model/seller.py
from django.contrib.auth.models import User
from django.db import models
from django.utils.text import slugify
from django.urls import reverse


SELLER_PLAN_CATALOG = [
    {
        "name": "Free",
        "slug": "free",
        "product_limit": 10,
        "media_limit": 1,
        "description": "Starter free seller plan.",
        "is_default": True,
        "price": 0,
    },
    {
        "name": "Starter",
        "slug": "starter",
        "product_limit": 50,
        "media_limit": 5,
        "description": "Ideal for new and growing sellers.",
        "is_default": False,
        "price": 999,
    },
    {
        "name": "Growth",
        "slug": "growth",
        "product_limit": 200,
        "media_limit": 12,
        "description": "For scaling multi-product stores.",
        "is_default": False,
        "price": 2499,
    },
]


def ensure_default_seller_plans():
    for plan_data in SELLER_PLAN_CATALOG:
        SellerPlan.objects.get_or_create(
            slug=plan_data["slug"],
            defaults=plan_data,
        )


class SellerPlan(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    product_limit = models.PositiveIntegerField(default=10)
    media_limit = models.PositiveIntegerField(default=1)
    description = models.TextField(blank=True)
    is_default = models.BooleanField(default=False)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        ordering = ["price", "product_limit"]

    @classmethod
    def get_default_plan(cls):
        return cls.objects.filter(is_default=True).first() or cls.objects.filter(price=0).order_by("id").first()

    @classmethod
    def resolve_plan(cls, plan_slug):
        if not plan_slug:
            return cls.get_default_plan()

        plan = cls.objects.filter(slug=plan_slug).first()
        return plan or cls.get_default_plan()

    @classmethod
    def get_plan_choices(cls):
        plans = cls.objects.order_by("price", "product_limit")
        choices = []
        for plan in plans:
            if plan.price == 0:
                label = "Free Plan"
            else:
                label = f"{plan.name} Plan - ₹{int(plan.price)} / month"
            choices.append((plan.slug, label))

        if not choices:
            choices = [("free", "Free Plan")]
        return choices

    def __str__(self):
        return self.name


class Seller(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    plan = models.ForeignKey(
        SellerPlan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sellers",
        default=None,
    )

    payment_mode = models.CharField(
        max_length=40,
        choices=[
            ("cod", "Cash on Delivery"),
            ("upi", "UPI"),
            ("card", "Card / Online Payment"),
            ("bank", "Bank Transfer"),
            ("whatsapp", "WhatsApp Order"),
        ],
        default="cod",
    )

    store_name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True, null=True)
    owner_name = models.CharField(max_length=200, blank=True)

    logo = models.ImageField(
        upload_to="uploads/seller/logos/",
        blank=True,
        null=True
    )

    banner = models.ImageField(
        upload_to="uploads/seller/banners/",
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
        null=True,
        help_text="Only include contry code and number, no spaces or special characters. Example: 919414053723"
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
            base_slug = slugify(self.store_name) or "seller"
            slug = base_slug
            counter = 1
            while Seller.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug

        super().save(*args, **kwargs)

    # for generating the URL for the seller's product listing page based on the seller's slug. 
    # This method is useful for creating links to the seller's products in templates and views.
    ## when you call seller.get_absolute_url(), it will return the URL for the seller's product listing page,
    ## which can be used in templates or redirects. 
    def get_absolute_url(self):

        return reverse(
            "seller_products",
            kwargs={
                "slug": self.slug
            }
        )
