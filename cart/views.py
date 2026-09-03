import json

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from urllib.parse import quote

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from .models import Cart, CartItem
from frontend.models import Products, Seller


# =========================================================
# ADD TO CART
# =========================================================

@require_POST
def ajax_add_to_cart(request):

    if not request.user.is_authenticated:
        return JsonResponse(
            {
                "status": "unauthenticated",
                "message": "Please login first."
            },
            status=401
        )

    try:
        data = json.loads(request.body)
        product_id = data.get("product_id")
    except (json.JSONDecodeError, TypeError):
        return JsonResponse(
            {
                "status": "error",
                "message": "Invalid request."
            },
            status=400
        )

    if not product_id:
        return JsonResponse(
            {
                "status": "error",
                "message": "Invalid product ID."
            },
            status=400
        )

    product = get_object_or_404(
        Products,
        id=product_id
    )

    # -----------------------------------------------------
    # STOCK CHECK
    # None = unlimited stock
    # -----------------------------------------------------

    if (
        product.stock_quantity is not None
        and product.stock_quantity <= 0
    ):
        return JsonResponse(
            {
                "status": "error",
                "message": "This product is currently out of stock."
            },
            status=400
        )

    cart, created = Cart.objects.get_or_create(
        user=request.user
    )

    existing_item = CartItem.objects.filter(
        cart=cart,
        product=product
    ).first()

    if existing_item:

        return JsonResponse(
            {
                "status": "info",
                "message": f"{product.name} is already in your cart."
            }
        )

    CartItem.objects.create(
        cart=cart,
        product=product,
        quantity=1
    )

    return JsonResponse(
        {
            "status": "success",
            "message": f"Added {product.name} to cart!"
        }
    )


# =========================================================
# CART DETAIL
# =========================================================

@login_required
def cart_detail(request):

    cart, created = Cart.objects.get_or_create(
        user=request.user
    )

    items = (
        cart.items
        .select_related(
            "product",
            "product__seller"
        )
        .prefetch_related(
            "product__media"
        )
    )

    # -----------------------------------------------------
    # IMPORTANT:
    # Synchronize old cart quantities with current stock.
    # -----------------------------------------------------

    for item in list(items):

        product = item.product
        stock = product.stock_quantity

        # Unlimited stock
        if stock is None:
            continue

        # Product completely out of stock
        if stock <= 0:

            item.delete()
            continue

        # Cart quantity greater than available stock
        if item.quantity > stock:

            item.quantity = stock
            item.save(
                update_fields=["quantity"]
            )

    # Re-read after synchronization
    items = (
        cart.items
        .select_related(
            "product",
            "product__seller"
        )
        .prefetch_related(
            "product__media"
        )
    )

    seller_groups = {}

    for item in items:

        seller = item.product.seller

        if not seller:
            continue

        if seller.id not in seller_groups:

            seller_groups[seller.id] = {
                "seller": seller,
                "items": [],
            }

        seller_groups[
            seller.id
        ]["items"].append(item)

    context = {
        "cart": cart,
        "seller_groups": seller_groups.values(),
        "cart_total": cart.total_price(),
    }

    return render(
        request,
        "cart/cart_detail.html",
        context
    )


# =========================================================
# REMOVE FROM CART
# =========================================================

@login_required
def remove_from_cart(request, item_id):

    item = get_object_or_404(
        CartItem,
        id=item_id,
        cart__user=request.user
    )

    item.delete()

    return redirect("cart_detail")


# =========================================================
# CART ITEM COUNT
# =========================================================

def cart_item_count(request):

    if request.user.is_authenticated:

        try:

            cart = Cart.objects.get(
                user=request.user
            )

            return JsonResponse(
                {
                    "count": cart.items.count()
                }
            )

        except Cart.DoesNotExist:

            return JsonResponse(
                {
                    "count": 0
                }
            )

    return JsonResponse(
        {
            "count": 0
        }
    )


# =========================================================
# UPDATE CART QUANTITY
# =========================================================

@login_required
@require_POST
def update_cart_quantity(request, item_id):

    item = get_object_or_404(
        CartItem,
        id=item_id,
        cart__user=request.user
    )

    # -----------------------------------------------------
    # READ JSON
    # -----------------------------------------------------

    try:

        if request.content_type == "application/json":

            data = json.loads(
                request.body.decode("utf-8")
            )

            quantity = int(
                data.get("quantity", 1)
            )

        else:

            quantity = int(
                request.POST.get(
                    "quantity",
                    1
                )
            )

    except (
        ValueError,
        TypeError,
        json.JSONDecodeError
    ):

        return JsonResponse(
            {
                "status": "error",
                "message": "Invalid quantity."
            },
            status=400
        )

    product = item.product

    stock = product.stock_quantity

    # =====================================================
    # PRODUCT OUT OF STOCK
    # =====================================================

    if stock is not None and stock <= 0:

        item.delete()

        return JsonResponse(
            {
                "status": "removed",
                "message":
                    f"{product.name} is now out of stock.",
                "cart_count":
                    item.cart.items.count()
            }
        )

    # =====================================================
    # QUANTITY LESS THAN 1
    # =====================================================

    if quantity < 1:

        quantity = 1

    # =====================================================
    # FIXED STOCK
    # =====================================================

    if stock is not None:

        # User cannot exceed available stock
        if quantity > stock:

            quantity = stock

            item.quantity = quantity

            item.save(
                update_fields=["quantity"]
            )

            return JsonResponse(
                {
                    "status": "limited",
                    "quantity": quantity,
                    "max_stock": stock,
                    "item_total": float(
                        item.total_price()
                    ),
                    "cart_total": float(
                        item.cart.total_price()
                    ),
                    "cart_count":
                        item.cart.items.count(),
                    "message":
                        f"Only {stock} available."
                }
            )

    # =====================================================
    # SAVE QUANTITY
    # =====================================================

    item.quantity = quantity

    item.save(
        update_fields=["quantity"]
    )

    return JsonResponse(
        {
            "status": "success",
            "quantity": item.quantity,
            "max_stock": stock,
            "item_total": float(
                item.total_price()
            ),
            "cart_total": float(
                item.cart.total_price()
            ),
            "cart_count":
                item.cart.items.count()
        }
    )


# =========================================================
# WHATSAPP SELLER
# =========================================================

@login_required
def whatsapp_seller(request, seller_id):

    # ---------------------------------------------------------
    # GET SELLER
    # ---------------------------------------------------------

    seller = get_object_or_404(
        Seller,
        id=seller_id
    )


    # ---------------------------------------------------------
    # GET CUSTOMER CART
    # ---------------------------------------------------------

    cart = get_object_or_404(
        Cart,
        user=request.user
    )


    # ---------------------------------------------------------
    # GET ONLY PRODUCTS BELONGING TO THIS SELLER
    # ---------------------------------------------------------

    items = (
        cart.items
        .select_related("product", "product__seller")
        .prefetch_related("product__media")
        .filter(
            product__seller=seller
        )
    )


    # ---------------------------------------------------------
    # NO PRODUCTS FROM THIS SELLER
    # ---------------------------------------------------------

    if not items.exists():

        messages.error(
            request,
            "There are no products from this seller in your cart."
        )

        return redirect("cart_detail")


    # ---------------------------------------------------------
    # CHECK SELLER WHATSAPP NUMBER
    # ---------------------------------------------------------

    whatsapp_number = (
        seller.whatsapp_number or ""
    ).strip()


    # ---------------------------------------------------------
    # BUILD PRODUCT INFORMATION
    # ---------------------------------------------------------

    product_rows = []

    whatsapp_lines = [
        f"Hello {seller.store_name},",
        "",
        "I am interested in these products:",
        ""
    ]


    for item in items:

        product = item.product

        requested_qty = item.quantity

        # -----------------------------------------------------
        # STOCK CHECK
        #
        # None = unlimited stock
        # 0    = out of stock
        # >0   = fixed stock
        # -----------------------------------------------------

        if product.stock_quantity is None:

            available_qty = "Unlimited"
            stock_status = "Unlimited stock"

        else:

            available_qty = product.stock_quantity

            if product.stock_quantity <= 0:

                stock_status = "OUT OF STOCK"

            elif requested_qty > product.stock_quantity:

                stock_status = (
                    f"Only {product.stock_quantity} available"
                )

            else:

                stock_status = "Available"


        # -----------------------------------------------------
        # PRODUCT IMAGE
        # -----------------------------------------------------

        image_url = None

        try:

            if product.primary_image:

                image_url = request.build_absolute_uri(
                    product.primary_image.file.url
                )

        except Exception:

            image_url = None


        # -----------------------------------------------------
        # PRODUCT TOTAL
        # -----------------------------------------------------

        item_total = (
            product.price * requested_qty
        )


        # -----------------------------------------------------
        # DATA FOR EMAIL TEMPLATE
        # -----------------------------------------------------

        product_rows.append({
            "id": product.id,
            "name": product.name,
            "quantity": requested_qty,
            "price": product.price,
            "item_total": item_total,
            "available_qty": available_qty,
            "stock_status": stock_status,
            "image_url": image_url,
        })


        # -----------------------------------------------------
        # WHATSAPP MESSAGE
        # -----------------------------------------------------

        whatsapp_lines.append(
            f"• Product ID: {product.id} | "
            f"{product.name} | "
            f"Qty: {requested_qty}"
        )


    # ---------------------------------------------------------
    # WHATSAPP MESSAGE FOOTER
    # ---------------------------------------------------------

    whatsapp_lines.extend([
        "",
        "Please let me know availability and further details.",
        "",
        f"Customer: {request.user.get_username()}"
    ])


    whatsapp_message = "\n".join(
        whatsapp_lines
    )


    # ---------------------------------------------------------
    # EMAIL CONTEXT
    # ---------------------------------------------------------

    customer_name = (
        request.user.get_full_name()
        or request.user.get_username()
    )

    customer_email = (
        request.user.email
    )


    email_context = {

        "seller": seller,

        "customer": request.user,

        "customer_name": customer_name,

        "customer_email": customer_email,

        "product_rows": product_rows,

        "cart": cart,

    }


    # ---------------------------------------------------------
    # SEND EMAIL TO SELLER but DO NOT BREAK WHATSAPP
    # ---------------------------------------------------------

    if seller.email:

        email_subject = (
            f"New Product Inquiry from {customer_name} "
            f"- {seller.store_name}"
        )


        email_html = render_to_string(
            "cart/seller_inquiry_email.html",
            email_context
        )


        email_text = (
            f"Hello {seller.store_name},\n\n"
            f"{customer_name} is interested in products "
            f"from your store.\n\n"
        )


        for row in product_rows:

            email_text += (
                f"Product ID: {row['id']}\n"
                f"Product: {row['name']}\n"
                f"Requested Quantity: {row['quantity']}\n"
                f"Available Quantity: {row['available_qty']}\n"
                f"Price: ₹{row['price']}\n"
                f"Status: {row['stock_status']}\n\n"
            )


        email_text += (
            f"Customer: {customer_name}\n"
            f"Email: {customer_email}\n"
        )


        email = EmailMultiAlternatives(

            subject=email_subject,

            body=email_text,

            from_email=None,

            to=[
                seller.email
            ],
        )


        email.attach_alternative(
            email_html,
            "text/html"
        )


        try:

            email.send(
                fail_silently=False
            )

            email_sent = True

        except Exception as e:

            import logging
            logger = logging.getLogger(__name__)

            logger.exception(
                "Email failed for seller %s: %s",
                seller.id,
                e
            )

            messages.warning(
                request,
                "WhatsApp will open, but the seller email could not be sent."
            )
            
            email_sent = False

    else:

        email_sent = False


    # ---------------------------------------------------------
    # WHATSAPP
    # ---------------------------------------------------------

    if whatsapp_number:

        # Remove spaces, + and other common formatting
        whatsapp_number = (
            whatsapp_number
            .replace(" ", "")
            .replace("-", "")
            .replace("(", "")
            .replace(")", "")
        )

        if whatsapp_number.startswith("+"):

            whatsapp_number = whatsapp_number[1:]


        whatsapp_url = (
            f"https://wa.me/"
            f"{whatsapp_number}"
            f"?text={quote(whatsapp_message)}"
        )


        # -----------------------------------------------------
        # OPTIONAL SUCCESS MESSAGE
        # -----------------------------------------------------

        if email_sent:

            messages.success(
                request,
                "Your product inquiry has also been emailed to the seller."
            )


        return redirect(
            whatsapp_url
        )


    # ---------------------------------------------------------
    # SELLER DOES NOT HAVE WHATSAPP
    # ---------------------------------------------------------

    if email_sent:

        messages.success(
            request,
            "The seller does not have a WhatsApp number. "
            "Your inquiry has been emailed to the seller."
        )

    else:

        messages.error(
            request,
            "This seller has no WhatsApp number or email address."
        )


    return redirect(
        "cart_detail"
    )