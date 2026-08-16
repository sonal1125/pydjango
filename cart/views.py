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
    
    # Use a manual if not request.user.is_authenticated check instead of @login_required, and return an explicit 401 for unauthenticated users.
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'unauthenticated'}, status=401)
    
    data = json.loads(request.body)
    product_id = data.get('product_id')

    if not product_id:
        return JsonResponse({'status': 'error', 'message': 'Invalid product ID'})

    try:
        product = Products.objects.get(id=product_id)
    except Products.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Product not found'})

    cart, created = Cart.objects.get_or_create(user=request.user)

    # If product already in cart, no duplicates allowed (optional)
    exists = CartItem.objects.filter(cart=cart, product=product).exists()
    if exists:
        return JsonResponse({'status': 'info', 'message': f'{product.name} already in cart!'})

    CartItem.objects.create(cart=cart, product=product)

    return JsonResponse({'status': 'success', 'message': f'Added {product.name} to cart!'})





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

    try:
        data = json.loads(request.body)
        quantity = int(data.get("quantity", 1))
    except (ValueError, TypeError, json.JSONDecodeError):
        return JsonResponse({
            "status": "error",
            "message": "Invalid quantity."
        }, status=400)

    if quantity < 1:
        item.delete()

        return JsonResponse({
            "status": "removed",
            "cart_count": item.cart.items.count()
        })

    item.quantity = quantity
    item.save(update_fields=["quantity"])

    return JsonResponse({
        "status": "success",
        "quantity": item.quantity,
        "item_total": float(
            item.product.price * item.quantity
        ),
        "cart_total": float(
            item.cart.total_price()
        ),
        "cart_count": item.cart.items.count()
    })

@login_required
def whatsapp_seller(request, seller_id):

    seller = get_object_or_404(
        Seller,
        id=seller_id
    )

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

    # Seller WhatsApp number
    whatsapp_number = seller.whatsapp_number

    if not whatsapp_number:
        messages.error(
            request,
            f"{seller.store_name} has not added a WhatsApp number yet."
        )
        return redirect("cart_detail")

    # Customer name
    customer_name = request.user.get_full_name()

    if not customer_name:
        customer_name = request.user.username

    # WhatsApp message
    message_lines = [
        f"Hello {seller.store_name},",
        "",
        "I am interested in these products:",
        ""
    ]

    for item in items:

        product = item.product

        message_lines.append(
            f"• Product ID: {product.id} | {product.name} — Qty: {item.quantity}"
        )

    message_lines.append("")
    message_lines.append(
        "Please let me know availability and further details."
    )

    message_lines.append("")
    message_lines.append(
        customer_name
    )

    message = "\n".join(message_lines)

    whatsapp_url = (
        f"https://wa.me/{whatsapp_number}"
        f"?text={quote(message)}"
    )

    return redirect(whatsapp_url)