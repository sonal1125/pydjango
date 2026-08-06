from django.contrib import admin 
from django.urls import path
from .views.home import Index 
from .views.signup import * 
from .views.contact import Contact
from .views.Product import *
from django.contrib.auth import views as auth_views  # ✅ required import
###from .middlewares.auth import auth_middleware 
from .views.seller import seller_products
from .views.About import About


#set dynamic urls

urlpatterns = [ 
	path('', Index.as_view(), name='homepage'), 
    path('products', product_all, name='product_all'),    
    path("aboutus", About, name="about"),
    path('contactus', Contact, name='contact'),
    path('<slug:slug>', product_list_by_category, name='product_list'),
	path("signup/", signup_view, name="signup"),
    # path('product/<int:product_id>/', product_detail, name='product_detail'),
    path("product/<slug:slug>/", product_detail, name="product_detail"),

	# Login/Logout
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
	# path('check-out', CheckOut.as_view(), name='checkout'), 
	#path('orders', auth_middleware(OrderView.as_view()), name='orders'), 
    path("seller/<int:seller_id>/",seller_products,name="seller_products"),
] 
