from itertools import product
import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Cart, CartItem
from frontend.models import Products, Seller
from django.contrib.auth.decorators import login_required
from urllib.parse import quote

# Create your views here.

# @login_required
# def add_to_cart(request, product_id):
#     product = get_object_or_404(Products, id=product_id)
#     cart, created = Cart.objects.get_or_create(user=request.user)
    
#     """ item, created = CartItem.objects.get_or_create(cart=cart, product=product)
#     if not created:
#         item.quantity += 1
#         item.save() """
    
#      # Check if product already in cart
#     if CartItem.objects.filter(cart=cart, product=product).exists():
#         messages.info(request, "This product is already in your cart.")
#     else:
#         CartItem.objects.create(cart=cart, product=product)
#         messages.success(request, "Product added to your cart.")

#     return redirect('cart_detail')

#@login_required -- which means unauthenticated users are automatically redirected to the login page by Django — but via a full-page redirect, not a JSON response with a 401 status.
@require_POST
def ajax_add_to_cart(request):

    if not request.user.is_authenticated:

        return JsonResponse(
            {'status': 'unauthenticated'},
            status=401
        )

    try:
        data = json.loads(
            request.body.decode("utf-8")
        )

    except (json.JSONDecodeError, UnicodeDecodeError):

        return JsonResponse({
            'status': 'error',
            'message': 'Invalid request.'
        }, status=400)


    product_id = data.get('product_id')

    if not product_id:

        return JsonResponse({
            'status': 'error',
            'message': 'Invalid product ID'
        })


    try:

        product = Products.objects.get(
            id=product_id
        )

    except Products.DoesNotExist:

        return JsonResponse({
            'status': 'error',
            'message': 'Product not found'
        })


    # ---------------------------------------
    # STOCK CHECK
    # ---------------------------------------

    if (
        product.stock_quantity is not None
        and product.stock_quantity < 1
    ):

        return JsonResponse({
            'status': 'error',
            'message': 'This product is currently out of stock.'
        })


    cart, created = Cart.objects.get_or_create(
        user=request.user
    )


    # ---------------------------------------
    # ALREADY IN CART
    # ---------------------------------------

    existing_item = CartItem.objects.filter(
        cart=cart,
        product=product
    ).first()


    if existing_item:

        return JsonResponse({
            'status': 'info',
            'message':
                f'{product.name} is already in your cart!'
        })


    # ---------------------------------------
    # ADD PRODUCT
    # ---------------------------------------

    CartItem.objects.create(
        cart=cart,
        product=product,
        quantity=1
    )


    return JsonResponse({
        'status': 'success',
        'message':
            f'Added {product.name} to cart!'
    })


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

    seller_groups = {}

    for item in items:

        seller = item.product.seller

        if seller.id not in seller_groups:
            seller_groups[seller.id] = {
                "seller": seller,
                "items": [],
            }

        seller_groups[seller.id]["items"].append(item)

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

@login_required
def remove_from_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    item.delete()
    return redirect('cart_detail')

def cart_item_count(request):
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            return JsonResponse({'count': cart.items.count()})
        except Cart.DoesNotExist:
            return JsonResponse({'count': 0})
    return JsonResponse({'count': 0})


@login_required
@require_POST
def update_cart_quantity(request, item_id):

    item = get_object_or_404(
        CartItem,
        id=item_id,
        cart__user=request.user
    )

    # ---------------------------------------
    # GET QUANTITY FROM REQUEST
    # ---------------------------------------

    try:

        if request.content_type == "application/json":

            data = json.loads(
                request.body.decode("utf-8")
            )

            quantity = int(
                data.get("quantity")
            )

        else:

            quantity = int(
                request.POST.get("quantity")
            )

    except (
        ValueError,
        TypeError,
        json.JSONDecodeError,
        UnicodeDecodeError
    ):

        return JsonResponse({
            "status": "error",
            "message": "Invalid quantity."
        }, status=400)


    # ---------------------------------------
    # MINIMUM QUANTITY
    # ---------------------------------------

    if quantity < 1:

        cart = item.cart

        item.delete()

        return JsonResponse({
            "status": "removed",
            "cart_count": cart.items.count()
        })


    # ---------------------------------------
    # CHECK PRODUCT STOCK
    # ---------------------------------------

    max_quantity = item.product.stock_quantity

    if max_quantity is not None:

        if quantity > max_quantity:

            return JsonResponse({
                "status": "error",
                "message":
                    f"Only {max_quantity} available."
            }, status=400)


    # ---------------------------------------
    # SAVE QUANTITY
    # ---------------------------------------

    item.quantity = quantity

    item.save(
        update_fields=["quantity"]
    )


    # ---------------------------------------
    # RESPONSE
    # ---------------------------------------

    return JsonResponse({

        "status": "success",

        "quantity": item.quantity,

        "item_total": float(
            item.product.price *
            item.quantity
        ),

        "cart_total": float(
            item.cart.total_price()
        ),

        "cart_count": item.cart.items.count(),

        "stock_quantity": max_quantity

    })

@login_required
def whatsapp_seller(request, seller_id):

    seller = get_object_or_404(
        Seller,
        id=seller_id
    )

    # Check whether seller has WhatsApp number
    if not seller.whatsapp_number:
        messages.warning(
            request,
            f"{seller.store_name} has not added a WhatsApp number yet."
        )
        return redirect("cart_detail")

    cart = get_object_or_404(
        Cart,
        user=request.user
    )

    items = (
        cart.items
        .select_related("product")
        .filter(product__seller=seller)
    )

    if not items.exists():
        messages.error(
            request,
            "There are no products from this seller in your cart."
        )
        return redirect("cart_detail")

    message_lines = [
        f"Hello {seller.store_name},",
        "",
        "I am interested in these products:",
        ""
    ]

    for item in items:

        product = item.product

        message_lines.append(
            f"• Product ID: {product.id} | "
            f"{product.name} — Qty: {item.quantity}"
        )

    message_lines.extend([
        "",
        "Please let me know availability and further details.",
        "",
        request.user.get_full_name() or request.user.username
    ])

    message = "\n".join(message_lines)

    whatsapp_url = (
        f"https://wa.me/{seller.whatsapp_number}"
        f"?text={quote(message)}"
    )

    return redirect(whatsapp_url)