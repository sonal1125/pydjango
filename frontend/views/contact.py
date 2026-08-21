from django.shortcuts import render, redirect, HttpResponseRedirect 
# used appname as models in sepetrate folder and * as many models are there
from frontend.models import *
from django.views import View
from frontend.forms import ContactMessageForm
from django.contrib import messages

#contact view
def Contact(request):

    # categories = Category.objects.all()

    if request.method == "POST":

        form = ContactMessageForm(request.POST)

        if form.is_valid():
         form.save()

         messages.success(request,"Thank you! Your message has been sent successfully.")

         return redirect("contact")

    else:

        form = ContactMessageForm()

    context = {
        # "categories": categories,
        "form": form,
    }

    return render(request, "contact.html", context)