from django.shortcuts import render, redirect 
from django.contrib.auth.hashers import check_password 
from frontend.models.customer import Customer 
from django.views import View 
from frontend.models.products import Products 
from frontend.models.orders import Order 
from frontend.middlewares.auth import auth_middleware 


class OrderView(View): 

	def get(self, request): 
		customer = request.session.get('customer') 
		orders = Order.get_orders_by_customer(customer) 
		print(orders) 
		return render(request, 'orders.html', {'orders': orders}) 
