from django.shortcuts import render, redirect, HttpResponseRedirect 
# used appname as models in sepetrate folder and * as many models are there
from frontend.models import *
from django.views import View 


# Create your views here. 
def Contact(request):
    categories = Category.objects.all()  # as 'context_processors' is set so not requied but kept for refrence
    return render(request, 'contact.html', {'categories':categories})
