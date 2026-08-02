from django.shortcuts import render
from frontend.models import Seller

def About(request):
    sellers = Seller.objects.all()

    context = {
        "sellers": sellers,
    }

    return render(request, "about.html", context)