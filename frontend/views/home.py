from django.shortcuts import render, redirect, HttpResponseRedirect 
# used appname as models in sepetrate folder and * as many models are there
from frontend.models import *
from django.views import View 


# Create your views here. 
class Index(View): 
	
	def post(self, request): 
		product = request.POST.get('product') 
		remove = request.POST.get('remove') 
		cart = request.session.get('cart') 
		if cart: 
			quantity = cart.get(product) 
			if quantity: 
				if remove: 
					if quantity <= 1: 
						cart.pop(product) 
					else: 
						cart[product] = quantity-1
				else: 
					cart[product] = quantity+1

			else: 
				cart[product] = 1
		else: 
			cart = {} 
			cart[product] = 1

		request.session['cart'] = cart 
		print('cart', request.session['cart']) 
		return redirect('homepage') 

	def get(self, request): 
		
		# products = None  # as now we are not showing products on Index or home page or starting page insted we showing articles
		categories = Category.get_all_categories() 
		articles = Articles.objects.filter(flag=True)

		# categoryID = request.GET.get('category') 
		# if categoryID: 
		# 	products = Products.get_all_products_by_categoryid(categoryID) 
		# else: 
		# 	products = Products.get_all_products() 

		data = {} 
		data['articles'] = articles
		data['categories'] = categories 

		print('you are : ', request.session.get('email')) 
		return render(request, 'index.html', data) 

# def store(request): 
# 	cart = request.session.get('cart') 
# 	if not cart: 
# 		request.session['cart'] = {} 
# 	products = None
# 	categories = Category.get_all_categories() 
# 	categoryID = request.GET.get('category') 
# 	if categoryID: 
# 		products = Products.get_all_products_by_categoryid(categoryID) 
# 	else: 
# 		products = Products.get_all_products() 

# 	data = {} 
# 	data['products'] = products 
# 	data['categories'] = categories 

# 	print('you are : ', request.session.get('email')) 
# 	return render(request, 'home.html', data) 






# # Create your views here.
# def products(request):
#     products = Products.objects.all()
#     return render(request, 'products.html', {'products':products})
