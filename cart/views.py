import json

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from urllib.parse import quote

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

    seller = get_object_or_404(
        Seller,
        id=seller_id
    )

    # -----------------------------------------------------
    # Seller has no WhatsApp number
    # -----------------------------------------------------

    if not seller.whatsapp_number:

        messages.warning(
            request,
            f"{seller.store_name} has not added a WhatsApp number."
        )

        return redirect("cart_detail")

    cart = get_object_or_404(
        Cart,
        user=request.user
    )

    items = list(
        cart.items
        .select_related("product")
        .filter(
            product__seller=seller
        )
    )

    # -----------------------------------------------------
    # Synchronize stock BEFORE WhatsApp
    # -----------------------------------------------------

    valid_items = []

    for item in items:

        product = item.product

        stock = product.stock_quantity

        # Out of stock
        if stock is not None and stock <= 0:

            item.delete()
            continue

        # Cart quantity greater than available stock
        if (
            stock is not None
            and item.quantity > stock
        ):

            item.quantity = stock

            item.save(
                update_fields=["quantity"]
            )

        valid_items.append(item)

    # -----------------------------------------------------
    # Nothing available
    # -----------------------------------------------------

    if not valid_items:

        messages.warning(
            request,
            f"There are no available products from {seller.store_name} in your cart."
        )

        return redirect("cart_detail")

    # =====================================================
    # WHATSAPP MESSAGE
    # =====================================================

    customer_name = (
        request.user.get_full_name()
        or request.user.username
    )

    message_lines = [

        f"Hello {seller.store_name},",

        "",

        "I am interested in these products:",

        ""
    ]

    for item in valid_items:

        product = item.product

        message_lines.append(
            f"• Product ID: {product.id} | "
            f"{product.name} — Qty: {item.quantity}"
        )

    message_lines.extend(
        [
            "",
            "Please let me know availability and further details.",
            "",
            customer_name,
        ]
    )

    message = "\n".join(
        message_lines
    )

    # -----------------------------------------------------
    # Clean WhatsApp number
    # -----------------------------------------------------

    whatsapp_number = (
        seller.whatsapp_number
        .replace("+", "")
        .replace(" ", "")
        .replace("-", "")
        .replace("(", "")
        .replace(")", "")
    )

    whatsapp_url = (
        f"https://wa.me/{whatsapp_number}"
        f"?text={quote(message)}"
    )

    return redirect(
        whatsapp_url
    )