# Create your views here. 
from django.shortcuts import render, get_object_or_404
from frontend.models import Category, Products, ProductDeleteOTP, Seller
from cart.models import *
# for pagination
from django.core.paginator import Paginator

from django.template.loader import render_to_string
from django.http import HttpResponse
from django.db.models import Q

def product_all(request):
      all_products  = None    
      all_products = Products.objects.order_by("-id")

    # ---------------------------------------
    # PAGINATION
    # ---------------------------------------
      # ✅ Add pagination logic here
      paginator = Paginator(all_products, 16)
      page_number = request.GET.get('page')
      products_page = paginator.get_page(page_number)

      cart_items = []
      if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            cart_items = cart.items.values_list('product_id', flat=True)
        except Cart.DoesNotExist:
            pass

    # ---------------------------------------
    # CONTEXT
    # ---------------------------------------

      # for paginating products and cart items in seller_products view, we need to pass the paginated products and cart items to the template context.    
      # This allows the template to display the correct subset of products for the current page and also show which products are in the user's cart.   
      context = {
        # 'categories': categories,
        'products': products_page,
        'cart_items': cart_items,
      }
    # ---------------------------------------
    # AJAX PAGINATION
    # ---------------------------------------
      # ✅ AJAX support for pagination (if using fetch)
      # when the request is made via AJAX (e.g., when the user clicks to go to the next page of products), we want to return just the HTML for the product grid instead of rendering the entire page. 
      # This allows for a smoother user experience, as only the relevant part of the page is updated without a full page reload.    
      if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string('products/product_grid.html', context, request=request)
        return HttpResponse(html)

    
    # return render(request, 'products/product_list.html', data)    
      return render(request, 'products/product_list.html', context)

def product_list_by_category(request, slug):

    category = get_object_or_404(
        Category,
        slug=slug
    )

    # -------------------------------------------------
    # GET THIS CATEGORY + ALL DESCENDANT CATEGORIES
    # -------------------------------------------------

    category_ids = {category.id}

    changed = True

    while changed:

        changed = False

        child_ids = set(
            Category.objects.filter(
                parent_id__in=category_ids
            ).values_list(
                "id",
                flat=True
            )
        )

        new_ids = child_ids - category_ids

        if new_ids:
            category_ids.update(new_ids)
            changed = True


    # -------------------------------------------------
    # GET PRODUCTS FROM THIS CATEGORY AND ALL CHILDREN
    # -------------------------------------------------

    product_qs = (
        Products.objects
        .filter(category_id__in=category_ids)
        .select_related("seller", "category")
        .prefetch_related("media")
        .order_by("-id")
    )


    # -------------------------------------------------
    # CART ITEMS
    # -------------------------------------------------

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


    # -------------------------------------------------
    # PAGINATION
    # -------------------------------------------------

    paginator = Paginator(
        product_qs,
        16
    )

    page_number = request.GET.get("page")

    products_page = paginator.get_page(
        page_number
    )


    context = {
        "products": products_page,
        "cart_items": cart_items,
        "current_category": category,
    }


    # -------------------------------------------------
    # AJAX
    # -------------------------------------------------

    if request.headers.get(
        "x-requested-with"
    ) == "XMLHttpRequest":

        html = render_to_string(
            "products/product_grid.html",
            context,
            request=request
        )

        return HttpResponse(html)


    return render(
        request,
        "products/product_list.html",
        context
    )

def product_detail(request, slug):
#     product = (
#     Products.objects
#     .select_related("seller", "category")
#     .prefetch_related("media")
#     .get(slug=slug)
# )
    product = get_object_or_404(
    Products,
    slug=slug
)
    cart_items = []
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            cart_items = cart.items.values_list('product_id', flat=True)
        except Cart.DoesNotExist:
            pass
    return render(request, 'products/product_detail.html', {'product': product,
    "cart_items": cart_items,})

def product_search(request):

    query = request.GET.get("q", "").strip()

    products = Products.objects.none()

    if query:

        products = (
            Products.objects
            .filter(
                Q(name__icontains=query)
                |
                Q(description__icontains=query)

                # CATEGORY
                |
                Q(category__name__icontains=query)

                # SELLER
                |
                Q(seller__store_name__icontains=query)
                |
                Q(seller__owner_name__icontains=query)
                |
                Q(seller__email__icontains=query)
                |
                Q(seller__phone__icontains=query)
                |
                Q(seller__whatsapp_number__icontains=query)
                |
                Q(seller__address__icontains=query)
                |
                Q(seller__city__icontains=query)
                |
                Q(seller__state__icontains=query)
                |
                Q(seller__website__icontains=query)
                |
                Q(seller__description__icontains=query)
            )
            .select_related(
                "category",
                "seller"
            )
            .prefetch_related(
                "media"
            )
            .distinct()
            .order_by("-id")
        )

    # PAGINATION
    paginator = Paginator(products, 16)

    page_number = request.GET.get("page")

    products_page = paginator.get_page(page_number)

    # CART ITEMS
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

    context = {
        "products": products_page,
        "cart_items": cart_items,
        "search_query": query,
    }

    # AJAX PAGINATION
    if request.headers.get(
        "x-requested-with"
    ) == "XMLHttpRequest":

        html = render_to_string(
            "products/product_grid.html",
            context,
            request=request
        )

        return HttpResponse(html)

    return render(
        request,
        "products/product_search.html",
        context
    )

""" What this searches

For example, if the customer searches:

rakhi

it can find a product where:

Product name contains rakhi
Product description contains rakhi
Category name contains rakhi
Seller store name contains rakhi
Seller owner name contains rakhi
Seller email contains rakhi
Seller phone contains rakhi
Seller WhatsApp number contains rakhi
Seller address contains rakhi
Seller city contains rakhi
Seller state contains rakhi
Seller website contains rakhi
Seller description contains rakhi """