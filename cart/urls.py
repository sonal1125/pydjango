from django.urls import path
from . import views

urlpatterns = [
    path('', views.cart_detail, name='cart_detail'),    
    path('add/', views.ajax_add_to_cart, name='ajax_add_to_cart'),
    path('count/', views.cart_item_count, name='cart_item_count'),
    path('remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
]
