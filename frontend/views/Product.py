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
from frontend.models import Category, Products

def product_all(request):
      products = None
      categories = Category.get_all_categories() 
      products = Products.get_all_products() 

      data = {} 
      data['products'] = products 
      data['categories'] = categories 
      
      return render(request, 'products.html', data) 
    

def product_list_by_category(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = Products.objects.filter(category=category)
    categories = Category.get_all_categories() 
    
    return render(request, 'products.html', {
        'categories': categories,
        'products': products,
    })