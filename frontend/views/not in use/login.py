from django.shortcuts import render, redirect, HttpResponseRedirect 
# from django.contrib.auth.forms import UserCreationForm
# from django.urls import reverse_lazy
# from django.views.generic import CreateView
from django.views import View 

def LoginView(request):        
	return redirect('registration/login.html')

def logout(request): 
	request.session.clear() 
	return redirect('homepage') 
