from django.shortcuts import render
# used appname as models in sepetrate folder and * as many models are there
from frontend.models import *

# Create your views here.
def products(request):
    products = Products.objects.all()
    return render(request, 'products.html', {'products':products})

@staticmethod
def get_all_products_by_categoryid(category_id): 
    if category_id: 
        return Products.objects.filter(category=category_id) 
    else: 
        return Products.get_all_products() 