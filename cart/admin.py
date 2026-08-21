from django.contrib import admin
from .models import Cart, CartItem
from frontend.models import Products, Seller
from django.utils.html import format_html
# Register your models here.

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0

    fields = (
        # "product.id",
        "product",                       
        "product_image",
        "quantity",
        "cart",
        # "product.seller",
        # "product.price",        
    )

    readonly_fields = (
        "product_image",
    )

    show_change_link = False

    def product_image(self, obj):

        if obj:

            media = obj.primary_image

            if media and media.file:

                return format_html(
                    '<img src="{}" '
                    'style="width:60px;height:60px;'
                    'object-fit:cover;border-radius:6px;">',
                    media.file.url
                )

        return "No image"

    product_image.short_description = "Image"


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'id')
    inlines = [CartItemInline]

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'product')
