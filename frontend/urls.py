from django.contrib import admin 
from django.urls import path
from .views.home import Index 
from .views.signup import * 
from .views.signup import (
    signup_view,
    send_signup_verification,
)
from .views.contact import Contact
from .views.Product import *
from django.contrib.auth import views as auth_views  # ✅ required import

from .views.seller import (
    seller_dashboard,
    seller_products,
    seller_update_inquiry_status,
    seller_product_detail,
    seller_product_delete,
    seller_add_product,
    seller_profile,
    seller_profile_edit,
    seller_plan_checkout,
)
from .views.About import About

#set dynamic urls

urlpatterns = [ 
	path('', Index.as_view(), name='homepage'), 
    path('products', product_all, name='product_all'),    
    path("seller/dashboard/", seller_dashboard, name="seller_dashboard"),
    path("seller/plan/<slug:slug>/", seller_plan_checkout, name="seller_plan_checkout"),
    path("seller/profile/", seller_profile, name="seller_profile"),
    path("seller/<slug:slug>/profile/", seller_profile, name="seller_profile_public"),
    path("seller/profile/edit/", seller_profile_edit, name="seller_profile_edit"),
    path("seller/products/add/", seller_add_product, name="seller_add_product"),
    path("seller/products/<slug:slug>/delete/", seller_product_delete, name="seller_product_delete"),
    path("seller/products/<slug:slug>/", seller_product_detail, name="seller_product_detail"),
    # Update inquiry status
    path(
        "inquiry/<int:inquiry_id>/status/",
        seller_update_inquiry_status,
        name="seller_update_inquiry_status"
    ),
    path("aboutus", About, name="about"),
    path('contactus', Contact, name='contact'),
    path(
    "search/",
    product_search,
    name="product_search"
),
    path('<slug:slug>', product_list_by_category, name='product_list'),
	path("signup/", signup_view, name="signup"),
    path(
    "signup/send-verification/",
    send_signup_verification,
    name="send_signup_verification",
),
    # path('product/<int:product_id>/', product_detail, name='product_detail'),
    path("product/<slug:slug>/", product_detail, name="product_detail"),
    path("seller/<slug:slug>/",seller_products,name="seller_products"),

	# Login/Logout
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
	# path('check-out', CheckOut.as_view(), name='checkout'), 
	#path('orders', auth_middleware(OrderView.as_view()), name='orders'), 
    
] 
