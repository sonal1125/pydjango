from django.shortcuts import render, get_object_or_404
from frontend.models import Seller, Products
from cart.models import Cart
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.http import HttpResponse


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