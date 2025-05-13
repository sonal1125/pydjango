from django.contrib import admin
from .models import *

class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name","slug",) # for display in admin panel
    prepopulated_fields = {"slug": ("name",)}

class ProductsAdmin(admin.ModelAdmin):
    list_display = ("name","price","description","image",)
    

# Register your models here.
admin.site.register(Category, CategoryAdmin)
admin.site.register(Products, ProductsAdmin)
admin.site.register(Articles)
admin.site.register(Customer)
admin.site.register(Order)

