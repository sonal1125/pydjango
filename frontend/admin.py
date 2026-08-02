from django.contrib import admin
from .models import *
from django.utils.html import mark_safe

from .models import ProductDeleteOTP
# from .models.productMedia import ProductMedia
from .models import ContactMessage
from django.urls import path
from django.shortcuts import render, redirect
from django.http import HttpResponse
import random
from django.core.mail import send_mail
from django.utils.html import format_html
from django.contrib.sites.shortcuts import get_current_site   #for sending image to mail otp
from django.contrib import messages
from frontend.models import (
    Products,
    ProductMedia,
    Seller,
    ProductDeleteOTP,
)
# Register your models here.

class ProductsInline(admin.TabularInline):
    model = Products
    extra = 1  # When editing a model that includes ProductsInline, Django will show one extra blank form for adding a new Products entry.

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name","id","slug") # for display in admin panel, id as second list item as first item in admin has list to open its edit pane
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductsInline]

"""     def has_delete_permission(self, request, obj=None):
       if obj:
            # Deny delete if category has products
            return not Products.objects.filter(category=obj).exists()
       return True """   #as doing with otp and its overrideein by second method so of no use
    

""" class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1 """ #as now using roductMedia model

class ProductMediaInline(admin.TabularInline):
    model = ProductMedia
    extra = 1

@admin.register(Products)
class ProductsAdmin(admin.ModelAdmin):
    inlines = [ProductMediaInline]
    list_display = ("name","id","category_name","price","description","seller","product_image",'request_otp_delete')
    exclude = [] # To show all fields unless overridden below
    actions = []  # Remove bulk delete action

    def category_name(self, obj):
        return obj.category.name  # Assumes Category model has a 'name' field
    
    category_name.admin_order_field = 'category'  # Optional: allows sorting
    category_name.short_description = 'Category Name'   #is used to set the column header name in the admin list view for the custom method category_name.

    def product_image(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="50" height="50" style="object-fit: cover;" />')
        return "No Image"
    product_image.short_description = "Image"

    # Hide 'seller' field for non-superusers
    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if not request.user.is_superuser:
            fields = [f for f in fields if f != 'seller']
        return fields

    # Auto-assign logged-in user as seller if not already set
    def save_model(self, request, obj, form, change):
        if not change or not obj.seller_id:
            try:
                seller = Seller.objects.get(user=request.user)
                obj.seller = seller
            except Seller.DoesNotExist:
                # Optionally handle this case
                raise ValueError("You must be a registered Seller to add a product.")
            
        super().save_model(request, obj, form, change)

        # Automatically create ProductMedia
        if obj.image and not obj.media.exists():
            ProductMedia.objects.create(
              product=obj,
              file=obj.image,  
              alt_text=obj.name,
              order=1,
            )

    # Show only the seller's own products unless superuser
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        try:
            seller = Seller.objects.get(user=request.user)
            return qs.filter(seller=seller)
        except Seller.DoesNotExist:
            return qs.none()        


    # Restrict edit/delete permissions to the product's seller or superuser
    def has_change_permission(self, request, obj=None):
        if obj is None or request.user.is_superuser:
            return True
        return obj.seller == request.user

    def has_delete_permission(self, request, obj=None):
        if obj is None or request.user.is_superuser:
            return True
        return obj.seller == request.user

    def get_readonly_fields(self, request, obj=None):
        if not request.user.is_superuser:
            return ['seller']
        return super().get_readonly_fields(request, obj)
    
    # If you want to block users who are not sellers from even seeing the product admin add page
    def has_add_permission(self, request):
        if request.user.is_superuser:
            return True
        return Seller.objects.filter(user=request.user).exists()

    
    # Disable default delete completely
    def has_delete_permission(self, request, obj=None):
        return False
    
    #code for delete product
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'request-delete/<int:product_id>/',
                self.admin_site.admin_view(self.request_delete_otp),
                name='frontend_products_request_delete_otp'
            ),
            path(
                'confirm-delete/<int:product_id>/',
                self.admin_site.admin_view(self.confirm_delete_otp),
                name='frontend_products_confirm_delete_otp'  # ✅ add this name
            ),
        ]
        return custom_urls + urls

    #delete request button on productlist
    def request_otp_delete(self, obj):
        return format_html('<a class="button" href="{}">Request Delete</a>', f'./request-delete/{obj.id}/')
    
    request_otp_delete.short_description = "Request OTP Deletion"
    request_otp_delete.allow_tags = True

    def request_delete_otp(self, request, product_id):
        product = Products.objects.get(id=product_id)
        otp = str(random.randint(100000, 999999))

        # Remove any existing OTPs for the same product & user
        ProductDeleteOTP.objects.filter(user=request.user, product=product).delete()
        
        # Now create a fresh one
        ProductDeleteOTP.objects.create(user=request.user, product=product, otp=otp)

        # Email content
        domain = get_current_site(request).domain        
        image_url = f'http://{domain}{product.image.url}' if product.image else "No image available"

        subject = 'OTP for Product Deletion (Admin)'

        plain_message = f'''
            OTP to confirm deletion of the following product:

            Product ID: {product.id}
            Name: {product.name}
            Category: {product.category.name}
            Price: ₹{product.price}
            Description: {product.description}
            Image URL: {image_url}

                OTP: {otp}

            This OTP will expire in 10 minutes.
            '''

        html_message = f'''
            <h2>OTP for Product Deletion</h2>
            <p><strong>Product ID:</strong> {product.id}</p>
            <p><strong>Name:</strong> {product.name}</p>
            <p><strong>Category:</strong> {product.category.name}</p>
            <p><strong>Price:</strong> ₹{product.price}</p>
            <p><strong>Description:</strong> {product.description}</p>
            <p><strong>Image:</strong><br><img src="{image_url}" width="300"></p>
            <h3 style="color: red;">OTP: {otp}</h3>
            <p><em>This OTP will expire in 10 minutes.</em></p>
            '''

        send_mail(
            subject,
            plain_message,
            'jonsa25@gmail.com',
            ['jonsa25@gmail.com'],
            html_message=html_message,
            fail_silently=False,
        )


        # send_mail(
        #     'OTP for Product Deletion (Admin)',
        #     f'Your OTP to confirm deletion of product "{product.name}" is: {otp}',
        #     'jonsa25@gmail.com',
        #     ['jonsa25@gmail.com'], #product.owner.email
        # )

        #return render(request, 'admin/confirm_delete_otp.html', {'product_id': product.id})
        return render(request, 'admin/confirm_delete_otp.html', {
            'product_id': product.id,
            'message': '✅ OTP sent successfully to your email.'
        })

    def confirm_delete_otp(self, request, product_id):
        if request.method == 'POST':
            entered_otp = request.POST.get('otp')
            try:
                otp_entry = ProductDeleteOTP.objects.get(product_id=product_id)
                if otp_entry.otp == entered_otp and not otp_entry.is_expired():
                    Products.objects.get(id=product_id).delete()
                    otp_entry.delete()
                    messages.success(request, "✅ Product deleted successfully.")
                    return redirect('admin:frontend_products_changelist')
                else:
                    messages.error(request, "❌ Invalid or expired OTP.")
            except ProductDeleteOTP.DoesNotExist:
                messages.error(request, "❌ No OTP request found.")

        return redirect('admin:frontend_products_changelist')


    
@admin.register(Articles)
class ArticlesAdmin(admin.ModelAdmin):
    list_display=("name","id","description","articles_image","flag")

    def articles_image(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="50" height="50" style="object-fit: cover;" />')
        return "No Image"
    articles_image.short_description = "Image"

# admin.site.register(Category, CategoryAdmin)
# admin.site.register(Products, ProductsAdmin)
# admin.site.register(Articles)
admin.site.register(Customer)
admin.site.register(Order)
admin.site.register(ProductDeleteOTP)
admin.site.register(Seller)

@admin.register(ProductMedia)
class ProductMediaAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "media_type",
        "order",
        "preview",
    )

    list_filter = ("media_type",)

    ordering = ("product", "order")

    def preview(self, obj):
        if obj.media_type == "image":
            return mark_safe(
                f'<img src="{obj.file.url}" width="80">'
            )
        return "Video"

    preview.short_description = "Preview"

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "email",
        "subject",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "created_at",
    )

    search_fields = (
        "name",
        "email",
        "subject",
    )

    ordering = ("-created_at",)