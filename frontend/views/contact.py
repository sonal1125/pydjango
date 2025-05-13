from django.shortcuts import render, redirect, HttpResponseRedirect 
# used appname as models in sepetrate folder and * as many models are there
from frontend.models import *
from django.views import View 


# Create your views here. 
def Contact(request):
    categories = Category.objects.all()
    return render(request, 'contact.html', {'categories':categories})
