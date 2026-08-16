from itertools import product

from django.contrib import admin
from .models import *
from django.utils.html import mark_safe

from .models import ProductDeleteOTP
# from .models.productMedia import ProductMedia
from .models import ContactMessage
from django.urls import path
from django.shortcuts import render, redirect
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    Table,
    TableStyle,
    PageBreak,
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import mm

from pathlib import Path
from io import BytesIO
from urllib.request import urlopen
from PIL import Image as PILImage
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
    seller,    
)
from django.conf import settings

from reportlab.pdfbase import pdfmetrics    #for rupee symbol
from reportlab.pdfbase.ttfonts import TTFont
import json

from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import FileField, ImageField
from django.utils import timezone
from django.utils.text import slugify

BASE_DIR = Path(__file__).resolve().parent.parent

pdfmetrics.registerFont(
    TTFont("DejaVuSans", str(BASE_DIR / "fonts" / "DejaVuSans.ttf"))
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
    

class ProductMediaInline(admin.TabularInline):
    model = ProductMedia
    extra = 1

@admin.register(Products)
class ProductsAdmin(admin.ModelAdmin):
    inlines = [ProductMediaInline]
    list_display = ("name","id","category_name","price","description","seller","product_image",'request_otp_delete')
    exclude = [] # To show all fields unless overridden below
    actions = ["generate_whatsapp_catalogue"] # Remove bulk delete action

    def category_name(self, obj):
        return obj.category.name  # Assumes Category model has a 'name' field
    
    category_name.admin_order_field = 'category'  # Optional: allows sorting
    category_name.short_description = 'Category Name'   #is used to set the column header name in the admin list view for the custom method category_name.

    def product_image(self, obj):

      first_media = obj.media.first()

      if first_media:
        return mark_safe(
            f'<img src="{first_media.file.url}" '
            'width="50" '
            'height="50" '
            'style="object-fit:cover;">'
        )

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
        """if not change or not obj.seller_id:
            try:
                seller = Seller.objects.get(user=request.user)
                obj.seller = seller
            except Seller.DoesNotExist:
                # Optionally handle this case
                raise ValueError("You must be a registered Seller to add a product.") """
        # Superuser/admin can save the seller selected in the form.
        # Do NOT replace the selected seller with the logged-in user's seller.
        
        super().save_model(request, obj, form, change)        

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
        return obj.seller.user == request.user

    def has_delete_permission(self, request, obj=None):
        if obj is None or request.user.is_superuser:
            return True
        return obj.seller.user == request.user

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
        first_media = product.media.first()

        image_url = first_media.file.url if first_media else "No Image available"

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
            settings.EMAIL_HOST_USER,
            [product.seller.email],
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
    
    @admin.action(description="Generate WhatsApp Catalogue PDF")
    def generate_whatsapp_catalogue(self, request, queryset):
        """
        Generate a PDF catalogue for the products selected in Django Admin.
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,rightMargin=15 * mm,
            leftMargin=15 * mm,
            topMargin=15 * mm,
            bottomMargin=15 * mm,
            )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "CatalogueTitle",
            parent=styles["Title"],
            fontName="DejaVuSans",
            alignment=TA_CENTER,
            fontSize=20,
            leading=24,
            spaceAfter=8,
            )

        subtitle_style = ParagraphStyle(
            "CatalogueSubtitle",
            parent=styles["Normal"],
            fontName="DejaVuSans",
            alignment=TA_CENTER,
            fontSize=12,
            leading=16,
            spaceAfter=15,
            )

        product_name_style = ParagraphStyle(
            "ProductName",
            parent=styles["Heading2"],
            fontName="DejaVuSans",
            alignment=TA_CENTER,
            fontSize=15,
            leading=18,
            spaceAfter=6,
            )

        normal_style = ParagraphStyle("ProductDescription",
                                      parent=styles["Normal"],
                                      fontName="DejaVuSans",
                                      fontSize=10,
                                      leading=14,
                                      alignment=TA_CENTER,
                                      )

        story = []

        # -------------------------------------------------
        # HEADER
        # -------------------------------------------------

        story.append(
            Paragraph(
                "JAIPUR GEMS AND ARTS",
                title_style
            )
        )

        story.append(
            Paragraph(
                "Handmade & Artistic Products",
                subtitle_style
            )
        )

        story.append(Spacer(1, 5 * mm))

        # -------------------------------------------------
        # PRODUCTS
        # -------------------------------------------------

        for product in queryset:

            # Product name
            story.append(
                Paragraph(
                    product.name,
                    product_name_style
                )
            )

            # Category
            category_name = (
                product.category.name
                if product.category
                else ""
            )

            story.append(
                Paragraph(
                    f"<b>Category:</b> {category_name}",
                    normal_style
                )
            )

            story.append(Spacer(1, 3 * mm))

            # -------------------------------------------------
            # PRODUCT IMAGE
            # -------------------------------------------------

            media = product.primary_image

            if media and media.file:

                try:

                    image_url = media.file.url

                    response = urlopen(
                        image_url,
                        timeout=15
                    )

                    image_data = response.read()

                    pil_image = PILImage.open(
                        BytesIO(image_data)
                    )

                    # Convert image to RGB/RGBA
                    if pil_image.mode not in ("RGB", "RGBA"):
                        pil_image = pil_image.convert("RGB")

                    image_buffer = BytesIO()

                    pil_image.thumbnail(
                       (1200, 1200)
                    )

                    pil_image.save(
                        image_buffer,
                        format="JPEG"
                    )

                    image_buffer.seek(0)

                    pdf_image = Image(
                        image_buffer,
                        width=100 * mm,
                        height=100 * mm,
                    )

                    # Preserve image proportion
                    pdf_image._restrictSize(
                        100 * mm,
                        100 * mm
                    )

                    story.append(pdf_image)

                except Exception as e:

                    story.append(
                        Paragraph(
                            "Image unavailable",
                            normal_style
                        )
                    )

                    print(
                        f"Could not load image "
                        f"for product {product.id}: {e}"
                    )

            else:

                story.append(
                    Paragraph(
                        "Image unavailable",
                        normal_style
                    )
                )

            story.append(Spacer(1, 5 * mm))

            # -------------------------------------------------
            # PRICE
            # -------------------------------------------------

            story.append(
                Paragraph(
                    f"<b>₹{product.price}</b>",
                    ParagraphStyle(
                        "Price",
                        parent=normal_style,
                        fontSize=16,
                        leading=20,
                    )
                )
            )

            story.append(Spacer(1, 3 * mm))

            # -------------------------------------------------
            # SELLER
            # -------------------------------------------------

            if product.seller:

                seller_name = getattr(
                    product.seller,
                    "store_name",
                    str(product.seller)
                )

                story.append(
                    Paragraph(
                        f"<b>Seller:</b> {seller_name}",
                        normal_style
                    )
                )

            # -------------------------------------------------
            # DESCRIPTION
            # -------------------------------------------------

            if product.description:

                story.append(
                    Spacer(1, 3 * mm)
                )

                story.append(
                    Paragraph(
                        product.description,
                        normal_style
                    )
                )

            story.append(
                Spacer(1, 10 * mm)
            )

            # Product separator
            story.append(
                Table(
                    [[""]],
                    colWidths=[170 * mm],
                    rowHeights=[0.5 * mm],
                    style=TableStyle([
                        (
                            "LINEABOVE",
                            (0, 0),
                            (-1, -1),
                            0.5,
                            colors.grey
                        )
                    ])
                )
            )

            story.append(
                Spacer(1, 10 * mm)
            )

            # One product per page
            story.append(PageBreak())

        # Remove final unnecessary page break
        if story and isinstance(story[-1], PageBreak):
            story.pop()

        doc.build(story)

        buffer.seek(0)

        response = HttpResponse(
            buffer.getvalue(),
            content_type="application/pdf"
        )

        response[
            "Content-Disposition"
        ] = 'attachment; filename="jaipur_gems_catalogue.pdf"'

        return response

    # generate_whatsapp_catalogue.short_description = (
    #     "Generate WhatsApp Catalogue PDF"
    #      )

    
@admin.register(Articles)
class ArticlesAdmin(admin.ModelAdmin):
    list_display=("name","id","description","articles_image","flag")

    def articles_image(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="50" height="50" style="object-fit: cover;" />')
        return "No Image"
    articles_image.short_description = "Image"


admin.site.register(Customer)
admin.site.register(Order)
admin.site.register(ProductDeleteOTP)

def serialize_model_field(obj, field):
    """
    Convert a Django model field into a JSON-safe value.
    """

    # ForeignKey / OneToOneField
    if field.is_relation:
        return getattr(obj, f"{field.name}_id")

    value = getattr(obj, field.name)

    # FileField / ImageField
    if isinstance(field, (FileField, ImageField)):
        return value.name if value else None

    return value

@admin.register(Seller)
class SellerAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "store_name",
        "user",
        "backup_product_count",
    )

    actions = [
        "backup_selected_seller",
    ]

    def backup_product_count(self, obj):
        return Products.objects.filter(seller=obj).count()

    backup_product_count.short_description = "Products"

    @admin.action(
        description="Backup selected seller"
    )
    def backup_selected_seller(self, request, queryset):

        # -------------------------------------------------
        # SECURITY
        # -------------------------------------------------

        if not request.user.is_superuser:
            self.message_user(
                request,
                "Only the administrator can create seller backups.",
                level=messages.ERROR,
            )
            return

        # -------------------------------------------------
        # ONLY ONE SELLER AT A TIME
        # -------------------------------------------------

        if queryset.count() != 1:
            self.message_user(
                request,
                "Please select exactly ONE seller for the backup.",
                level=messages.ERROR,
            )
            return

        seller = queryset.first()

        # -------------------------------------------------
        # SELLER DATA
        # -------------------------------------------------

        seller_data = {
            "model": "frontend.seller",
            "id": seller.id,
            "fields": {},
        }

        # Automatically collect seller fields
        for field in seller._meta.fields:

            seller_data["fields"][field.name] = (
                serialize_model_field(seller, field)
            )

        # -------------------------------------------------
        # PRODUCT DATA
        # -------------------------------------------------

        products_data = []

        products = Products.objects.filter(
            seller=seller
        ).order_by("id")

        for product in products:

            product_data = {
                "model": "frontend.products",
                "id": product.id,
                "fields": {},
                "media": [],
            }

            # Product fields
            for field in product._meta.fields:

                product_data["fields"][field.name] = (
                    serialize_model_field(product, field)
                )

            # -------------------------------------------------
            # PRODUCT MEDIA
            # -------------------------------------------------

            media_items = ProductMedia.objects.filter(
                product=product
            ).order_by("order", "id")

            for media in media_items:

                media_data = {
                    "id": media.id,
                    "fields": {},
                }

                for field in media._meta.fields:

                    media_data["fields"][field.name] = (
                        serialize_model_field(media, field)
                    )

                product_data["media"].append(
                    media_data
                )

            products_data.append(
                product_data
            )

        # -------------------------------------------------
        # FINAL BACKUP
        # -------------------------------------------------

        backup = {
            "backup_type": "seller",
            "backup_version": "1.0",
            "created_at": timezone.now(),
            "seller": seller_data,
            "products": products_data,
            "summary": {
                "seller_id": seller.id,
                "product_count": len(products_data),
                "media_count": sum(
                    len(product["media"])
                    for product in products_data
                ),
            },
        }

        # -------------------------------------------------
        # JSON RESPONSE
        # -------------------------------------------------

        json_data = json.dumps(
            backup,
            cls=DjangoJSONEncoder,
            indent=4,
            ensure_ascii=False,
        )

        store_name = getattr(
            seller,
            "store_name",
            f"seller_{seller.id}"
        )

        safe_name = slugify(store_name)

        if not safe_name:
            safe_name = f"seller_{seller.id}"

        timestamp = timezone.localtime().strftime(
            "%Y%m%d_%H%M%S"
        )

        filename = (
            f"seller_backup_"
            f"{safe_name}_"
            f"{timestamp}.json"
        )

        response = HttpResponse(
            json_data,
            content_type="application/json; charset=utf-8",
        )

        response[
            "Content-Disposition"
        ] = (
            f'attachment; filename="{filename}"'
        )

        return response

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