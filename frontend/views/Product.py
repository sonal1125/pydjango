# comment as shortcut manner of getting products list on the bases of category slug

""" from django.shortcuts import render, redirect, HttpResponseRedirect 
# from django.views.generic import DetailView
# used appname as models in sepetrate folder and * as many models are there
from frontend.models import *
from django.views import View 


# Create your views here. 
class Product_list(View):
     
   def get(self, request): 
      categoryID = request.GET.get('category') 
      if categoryID: 
         products = Products.get_all_products_by_categoryid(categoryID) 
      else: 
         products = Products.get_all_products()    
    
      template_name = "Products.html"
 



# Product_list.get_queryset().

"""
# end comment



from django.shortcuts import render, get_object_or_404
from frontend.models import Category, Products, ProductDeleteOTP
from cart.models import *
# for pagination
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.http import HttpResponse

def product_all(request):
      all_products  = None
      categories = Category.get_all_categories() 
      all_products  = Products.get_all_products() 

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

      """ data = {} 
      data['products'] = products 
      data['categories'] = categories 
      data['cart_items'] = cart_items  """

      context = {
        'categories': categories,
        'products': products_page,
        'cart_items': cart_items,
      }

      if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string('product_grid_partial.html', context, request=request)
        return HttpResponse(html)
      
    #   return render(request, 'products.html', data)
      return render(request, 'products.html', context)

def product_list_by_category(request, slug):
    category = get_object_or_404(Category, slug=slug)
    product_qs = Products.objects.filter(category=category)
    categories = Category.get_all_categories()
    cart_items = []

    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            cart_items = cart.items.values_list('product_id', flat=True)
        except Cart.DoesNotExist:
            pass

    # ✅ Add pagination logic here
    paginator = Paginator(product_qs, 16)
    page_number = request.GET.get('page')
    products_page = paginator.get_page(page_number)

    context = {
        'categories': categories,
        'products': products_page,
        'cart_items': cart_items,
        'current_category': category,  # Optional: for highlighting/filtering
    }

    # ✅ AJAX support for pagination (if using fetch)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string('product_grid_partial.html', context, request=request)
        return HttpResponse(html)

    return render(request, 'products.html', context)


def product_detail(request, product_id):
    product = get_object_or_404(Products, id=product_id)
    return render(request, 'product_detail.html', {'product': product})