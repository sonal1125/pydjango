from django.shortcuts import render, get_object_or_404
from frontend.models import Seller, Products


def seller_products(request, seller_id):
    seller = get_object_or_404(Seller, id=seller_id)

    products = Products.objects.filter(
        seller=seller
    ).prefetch_related("media")

    return render(
        request,
        "seller/seller_products.html",
        {
            "seller": seller,
            "products": products,
        },
    )