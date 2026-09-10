import logging
import random

import resend
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from frontend.models import Inquiry, Seller, SellerPlan, Products, ProductDeleteOTP, ProductMedia
from frontend.forms import ProductForm, SellerProfileForm
from cart.models import Cart
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.contrib import messages
from django.db.models import Sum, Q
from django.contrib.auth.decorators import login_required


def seller_products(request, slug):

    seller = get_object_or_404(
        Seller,
        slug=slug
    )

    # ---------------------------------------
    # SELLER PRODUCTS
    # ---------------------------------------

    products = (
        Products.objects
        .filter(seller=seller)
        .order_by("-id")
        .prefetch_related("media")
    )


    # ---------------------------------------
    # CART ITEMS
    # ---------------------------------------

    cart_items = []

    if request.user.is_authenticated:

        try:

            cart = Cart.objects.get(
                user=request.user
            )

            cart_items = cart.items.values_list(
                "product_id",
                flat=True
            )

        except Cart.DoesNotExist:

            pass


    # ---------------------------------------
    # PAGINATION
    # ---------------------------------------

    paginator = Paginator(
        products,
        16
    )

    page_number = request.GET.get(
        "page"
    )

    products_page = paginator.get_page(
        page_number
    )


    # ---------------------------------------
    # CONTEXT
    # ---------------------------------------

    # for paginating products and cart items in seller_products view, we need to pass the paginated products and cart items to the template context.    
    # This allows the template to display the correct subset of products for the current page and also show which products are in the user's cart.   
    context = {

        "seller": seller,

        "products": products_page, # paginated page of products

        "cart_items": cart_items,

    }


    # ---------------------------------------
    # AJAX PAGINATION
    # ---------------------------------------
    # when the request is made via AJAX (e.g., when the user clicks to go to the next page of products), we want to return just the HTML for the product grid instead of rendering the entire page. 
    # This allows for a smoother user experience, as only the relevant part of the page is updated without a full page reload.    
    if request.headers.get(
        "x-requested-with"
    ) == "XMLHttpRequest":

        html = render_to_string(
            "products/product_grid.html",
            context,
            request=request
        )

        return HttpResponse(html)


    # ---------------------------------------
    # NORMAL PAGE
    # ---------------------------------------

    return render(
        request,
        "seller/seller_products.html",
        context
    )

# =========================================================
# SELLER DASHBOARD V2
# =========================================================

@login_required
def seller_dashboard(request):

    # -----------------------------------------------------
    # GET SELLER PROFILE FOR LOGGED-IN USER
    # -----------------------------------------------------

    try:

        seller = Seller.objects.get(
            user=request.user
        )

    except Seller.DoesNotExist:

        messages.error(
            request,
            "Your account is not linked to a seller profile."
        )

        return redirect("home")


    # -----------------------------------------------------
    # SELLER PRODUCTS
    # -----------------------------------------------------

    product_search_query = request.GET.get("product_q", "").strip()

    product_queryset = (
        Products.objects
        .filter(seller=seller)
        .order_by("name")
    )

    if product_search_query:
        product_queryset = product_queryset.filter(
            Q(name__icontains=product_search_query)
            | Q(description__icontains=product_search_query)
            | Q(category__name__icontains=product_search_query)
        )

    try:
        product_per_page = int(request.GET.get("product_per_page", "10"))
    except (TypeError, ValueError):
        product_per_page = 10

    if product_per_page not in (10, 20, 50):
        product_per_page = 10

    # -----------------------------------------------------
    # PRODUCT PAGINATION
    # -----------------------------------------------------

    product_paginator = Paginator(product_queryset, product_per_page)
    product_page_number = request.GET.get("product_page")
    products = product_paginator.get_page(product_page_number)


    # -----------------------------------------------------
    # PRODUCT COUNT
    # -----------------------------------------------------

    product_count = product_queryset.count()


    # -----------------------------------------------------
    # TOTAL STOCK
    #
    # None = Unlimited stock
    # -----------------------------------------------------

    unlimited_stock = product_queryset.filter(
        stock_quantity__isnull=True
    ).exists()


    if unlimited_stock:

        total_stock = "Unlimited"

    else:

        total_stock = (
            product_queryset.aggregate(
                total=Sum("stock_quantity")
            )["total"]
            or 0
        )


    # -----------------------------------------------------
    # SEARCH INQUIRIES
    # -----------------------------------------------------

    search_query = request.GET.get(
        "q",
        ""
    ).strip()


    # -----------------------------------------------------
    # STATUS FILTER
    # -----------------------------------------------------

    status_filter = request.GET.get(
        "status",
        ""
    ).strip()


    # -----------------------------------------------------
    # SELLER INQUIRIES
    # -----------------------------------------------------

    inquiries = (
        Inquiry.objects
        .filter(seller=seller)
        .select_related("customer")
        .prefetch_related(
            "items"
        )
        .order_by("-created_at")
    )


    # -----------------------------------------------------
    # SEARCH
    # -----------------------------------------------------

    if search_query:

        inquiries = inquiries.filter(

            Q(
                customer__username__icontains=search_query
            )

            |

            Q(
                customer__first_name__icontains=search_query
            )

            |

            Q(
                customer__last_name__icontains=search_query
            )

            |

            Q(
                customer__email__icontains=search_query
            )

            |

            Q(
                items__product_name__icontains=search_query
            )
        ).distinct()


    # -----------------------------------------------------
    # STATUS FILTER
    # -----------------------------------------------------

    if status_filter:

        inquiries = inquiries.filter(
            status=status_filter
        ).distinct()


    inquiry_paginator = Paginator(inquiries, 10)
    inquiry_page_number = request.GET.get("inquiry_page")
    inquiries = inquiry_paginator.get_page(inquiry_page_number)


    # -----------------------------------------------------
    # NEW INQUIRY COUNT
    # -----------------------------------------------------

    new_inquiry_count = Inquiry.objects.filter(
        seller=seller,
        status=Inquiry.STATUS_NEW
    ).count()


    # -----------------------------------------------------
    # TOTAL INQUIRY COUNT
    # -----------------------------------------------------

    inquiry_count = Inquiry.objects.filter(
        seller=seller
    ).count()


    # -----------------------------------------------------
    # PRESERVE FILTER PARAMS IN PAGINATION LINKS
    # -----------------------------------------------------

    query_params = request.GET.copy()
    query_params.pop("product_page", None)
    query_params.pop("inquiry_page", None)
    query_string = query_params.urlencode()


    # -----------------------------------------------------
    # CONTEXT
    # -----------------------------------------------------

    context = {

        "seller": seller,

        "products": products,

        "product_count": product_count,

        "total_stock": total_stock,

        "new_inquiry_count": new_inquiry_count,

        "inquiry_count": inquiry_count,

        "inquiries": inquiries,

        "search_query": search_query,

        "status_filter": status_filter,

        "status_choices": Inquiry.STATUS_CHOICES,

        "product_search_query": product_search_query,

        "product_per_page": product_per_page,

        "query_string": query_string,

    }


    return render(
        request,
        "seller/dashboard.html",
        context
    )


@login_required
def seller_add_product(request):
    try:
        seller = Seller.objects.get(user=request.user)
    except Seller.DoesNotExist:
        messages.error(
            request,
            "Your account is not linked to a seller profile."
        )
        return redirect("home")

    seller_plan = (
        seller.plan
        or SellerPlan.objects.filter(is_default=True).first()
        or SellerPlan.objects.create(
            name="Free",
            slug="free",
            product_limit=10,
            media_limit=1,
            description="Free plan",
            is_default=True,
        )
    )

    if request.method == "POST":

        form = ProductForm(
            request.POST,
            request.FILES
        )

        uploaded_files = request.FILES.getlist("images")

        # -----------------------------------------
        # PRODUCT LIMIT
        # -----------------------------------------

        if seller.products.count() >= seller_plan.product_limit:
            form.add_error(
                None,
                f"Your {seller_plan.name} plan allows only "
                f"{seller_plan.product_limit} products. "
                f"Upgrade to add more products."
            )

        # -----------------------------------------
        # IMAGE LIMIT
        # -----------------------------------------

        if len(uploaded_files) < 1:
            form.add_error(
                "images",
                "Please upload at least one product image."
            )

        elif len(uploaded_files) > seller_plan.media_limit:
            form.add_error(
                "images",
                f"Your {seller_plan.name} plan allows "
                f"only {seller_plan.media_limit} image(s) "
                f"per product. You selected "
                f"{len(uploaded_files)}."
            )

        # -----------------------------------------
        # SAVE PRODUCT
        # -----------------------------------------

        if form.is_valid() and not form.errors:

            product = form.save(commit=False)
            product.seller = seller
            product.save()

            # Save only the number permitted by the plan.
            # Normally this is already guaranteed by validation.
            allowed_files = uploaded_files[
                :seller_plan.media_limit
            ]

            for index, uploaded_file in enumerate(
                allowed_files,
                start=1
            ):
                ProductMedia.objects.create(
                    product=product,
                    file=uploaded_file,
                    media_type="image",
                    order=index,
                )

            messages.success(
                request,
                f"{product.name} added successfully."
            )

            return redirect(
                "seller_product_detail",
                slug=product.slug
            )

    else:
        form = ProductForm()

    return render(
        request,
        "seller/add_product.html",
        {
            "seller": seller,
            "form": form,
            "seller_plan": seller_plan,
        },
    )

@login_required
def seller_product_detail(request, slug):
    try:
        seller = Seller.objects.get(user=request.user)
    except Seller.DoesNotExist:
        messages.error(request, "Your account is not linked to a seller profile.")
        return redirect("home")

    product = get_object_or_404(Products, seller=seller, slug=slug)

    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        uploaded_files = list(request.FILES.getlist("images"))
        if form.is_valid():
            updated_product = form.save()
            if uploaded_files:
                for index, uploaded_file in enumerate(uploaded_files[: seller.plan.media_limit if seller.plan else 1], start=1):
                    ProductMedia.objects.create(
                        product=updated_product,
                        file=uploaded_file,
                        media_type="image",
                        order=(updated_product.media.count() + index),
                    )
            messages.success(request, f"{updated_product.name} updated successfully.")
            return redirect("seller_product_detail", slug=updated_product.slug)
    else:
        form = ProductForm(instance=product)

    return render(request, "seller/product_detail.html", {"seller": seller, "product": product, "form": form})


@login_required
def seller_product_delete(request, slug):
    try:
        seller = Seller.objects.get(user=request.user)
    except Seller.DoesNotExist:
        messages.error(request, "Your account is not linked to a seller profile.")
        return redirect("home")

    product = get_object_or_404(Products, seller=seller, slug=slug)

    otp_value = request.POST.get("otp")
    if otp_value:
        otp_entry = (
            ProductDeleteOTP.objects
            .filter(user=request.user, product=product)
            .order_by("-created_at")
            .first()
        )

        if otp_entry and otp_entry.otp == otp_value and not otp_entry.is_expired():
            product_name = product.name
            product.delete()
            otp_entry.delete()
            messages.success(request, f"{product_name} deleted successfully.")
            return redirect("seller_dashboard")

        messages.error(request, "Invalid or expired OTP. Please request a fresh one.")
        return render(request, "seller/confirm_delete_otp.html", {
            "product": product,
            "product_id": product.id,
            "slug": slug,
            "error": "Invalid or expired OTP. Please request a fresh one.",
        })

    if request.method != "POST":
        return redirect("seller_dashboard")

    otp = str(random.randint(100000, 999999))
    ProductDeleteOTP.objects.filter(user=request.user, product=product).delete()
    ProductDeleteOTP.objects.create(user=request.user, product=product, otp=otp)

    first_media = product.media.first()
    image_url = request.build_absolute_uri(first_media.file.url) if first_media and first_media.file else ""

    subject = f"OTP to delete product: {product.name}"
    html_message = f"""
        <h2>OTP to confirm product deletion</h2>
        <p><strong>Product:</strong> {product.name}</p>
        <p><strong>Price:</strong> ₹{product.price}</p>
        <p><strong>Category:</strong> {product.category.name}</p>
        <p><strong>Description:</strong> {product.description}</p>
        {f'<p><strong>Image:</strong><br><img src="{image_url}" width="300"></p>' if image_url else '<p><strong>Image:</strong> No image available</p>'}
        <h3 style="color: red;">OTP: {otp}</h3>
        <p><em>This OTP will expire in 10 minutes.</em></p>
    """
    plain_message = f"""
        OTP to confirm deletion of product: {product.name}
        Product ID: {product.id}
        Price: ₹{product.price}
        OTP: {otp}
        This OTP will expire in 10 minutes.
    """

    try:
        if not settings.RESEND_API_KEY:
            raise ValueError("RESEND_API_KEY is not configured.")
        resend.api_key = settings.RESEND_API_KEY
        resend.Emails.send({
            "from": settings.DEFAULT_FROM_EMAIL,
            "to": [seller.email],
            "subject": subject,
            "html": html_message,
            "text": plain_message,
        })
    except Exception as exc:
        logger = logging.getLogger(__name__)
        logger.exception("Seller product OTP email failed for %s: %s", product.id, exc)
        messages.error(request, "Could not send the OTP email. Please try again or check your email settings.")
        return redirect("seller_dashboard")

    return render(request, "seller/confirm_delete_otp.html", {
        "product": product,
        "product_id": product.id,
        "slug": slug,
        "message": "✅ OTP sent successfully to your email.",
    })


def seller_profile(request, slug=None):
    if slug:
        seller = get_object_or_404(Seller, slug=slug)
        is_owner = request.user.is_authenticated and getattr(request.user, "seller", None) and request.user.seller.id == seller.id
    else:
        if not request.user.is_authenticated:
            return redirect("login")
        try:
            seller = Seller.objects.get(user=request.user)
        except Seller.DoesNotExist:
            messages.error(request, "Your account is not linked to a seller profile.")
            return redirect("home")
        is_owner = True

    return render(request, "seller/profile.html", {"seller": seller, "is_owner": is_owner})


@login_required
def seller_profile_edit(request):
    try:
        seller = Seller.objects.get(user=request.user)
    except Seller.DoesNotExist:
        messages.error(request, "Your account is not linked to a seller profile.")
        return redirect("home")

    if request.method == "POST":
        form = SellerProfileForm(request.POST, request.FILES, instance=seller)
        if form.is_valid():
            form.save()
            messages.success(request, "Seller profile updated successfully.")
            return redirect("seller_profile")
    else:
        form = SellerProfileForm(instance=seller)

    return render(request, "seller/edit_profile.html", {"seller": seller, "form": form})


@login_required
def seller_plan_checkout(request, slug):
    seller = get_object_or_404(Seller, slug=slug, user=request.user)
    plans = SellerPlan.objects.order_by("price", "product_limit")
    selected_plan = seller.plan or SellerPlan.get_default_plan() or plans.first()

    if request.method == "POST":
        plan_slug = request.POST.get("plan_slug")
        chosen_plan = SellerPlan.resolve_plan(plan_slug) if plan_slug else selected_plan
        seller.plan = chosen_plan
        seller.save(update_fields=["plan"])
        messages.success(request, f"Your seller plan has been updated to {chosen_plan.name}.")
        return redirect("seller_dashboard")

    return render(
        request,
        "seller/plan_checkout.html",
        {
            "seller": seller,
            "plans": plans,
            "selected_plan": selected_plan,
        },
    )

# =========================================================
# SELLER UPDATE INQUIRY STATUS
# =========================================================

@login_required
def seller_update_inquiry_status(
    request,
    inquiry_id
):

    # -----------------------------------------------------
    # ONLY POST REQUESTS
    # -----------------------------------------------------

    if request.method != "POST":

        return redirect(
            "seller_dashboard"
        )


    # -----------------------------------------------------
    # GET CURRENT SELLER
    # -----------------------------------------------------

    try:

        seller = Seller.objects.get(
            user=request.user
        )

    except Seller.DoesNotExist:

        messages.error(
            request,
            "Your account is not linked to a seller profile."
        )

        return redirect("home")


    # -----------------------------------------------------
    # IMPORTANT SECURITY CHECK
    #
    # Seller can update ONLY THEIR OWN inquiry
    # -----------------------------------------------------

    inquiry = get_object_or_404(
        Inquiry,
        id=inquiry_id,
        seller=seller
    )


    # -----------------------------------------------------
    # GET NEW STATUS
    # -----------------------------------------------------

    new_status = request.POST.get(
        "status"
    )


    # -----------------------------------------------------
    # VALID STATUS CHECK
    # -----------------------------------------------------

    valid_statuses = dict(
        Inquiry.STATUS_CHOICES
    )


    if new_status not in valid_statuses:

        messages.error(
            request,
            "Invalid inquiry status."
        )

        return redirect(
            "seller_dashboard"
        )


    # -----------------------------------------------------
    # UPDATE
    # -----------------------------------------------------

    inquiry.status = new_status

    inquiry.save(
        update_fields=[
            "status"
        ]
    )


    messages.success(
        request,
        f"Inquiry #{inquiry.id} updated to "
        f"{valid_statuses[new_status]}."
    )


    # -----------------------------------------------------
    # RETURN TO DASHBOARD
    # -----------------------------------------------------

    return redirect(
        "seller_dashboard"
    )