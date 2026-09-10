import random

from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.db import transaction

from frontend.forms import SignupForm
from frontend.models import Seller, SellerPlan
from frontend.models.seller import ensure_default_seller_plans

from django.http import JsonResponse
from django.contrib.auth.models import User

def _send_email_verification(request, email):

    email = email.strip().lower()

    code = str(
        random.randint(100000, 999999)
    )

    request.session["pending_email_verification"] = {
        "email": email,
        "code": code,
        "verified": False,
    }

    request.session.modified = True

    send_mail(
        subject="Your Jaipur Gems & Arts verification code",

        message=(
            "Your email verification code is: "
            f"{code}\n\n"
            "Enter this code on the signup page "
            "to verify your email address."
        ),

        from_email=settings.DEFAULT_FROM_EMAIL,

        recipient_list=[email],

        fail_silently=False,
    )

    return code

def send_signup_verification(request):

    if request.method != "POST":
        return JsonResponse(
            {
                "success": False,
                "message": "Invalid request."
            },
            status=405
        )

    email = (
        request.POST.get("email") or ""
    ).strip().lower()

    if not email:
        return JsonResponse(
            {
                "success": False,
                "message": "Please enter your email address."
            },
            status=400
        )

    # -----------------------------------------
    # CHECK EMAIL ALREADY REGISTERED
    # -----------------------------------------

    if User.objects.filter(
        email__iexact=email
    ).exists():

        return JsonResponse(
            {
                "success": False,
                "message": (
                    "This email address is already registered. "
                    "Please use another email or log in."
                ),
                "already_registered": True,
            },
            status=400
        )

    # -----------------------------------------
    # SEND CODE
    # -----------------------------------------

    try:

        _send_email_verification(
            request,
            email
        )

    except Exception:

        return JsonResponse(
            {
                "success": False,
                "message": (
                    "We could not send the verification email "
                    "right now. Please try again."
                ),
            },
            status=500
        )

    return JsonResponse(
        {
            "success": True,
            "message": (
                "Verification code sent to your email. "
                "Please check your inbox."
            ),
        }
    )

def signup_view(request):

    ensure_default_seller_plans()

    if request.method == "POST":

        form = SignupForm(
            request.POST,
            request=request
        )

        if form.is_valid():

            with transaction.atomic():

                user = form.save()

                account_type = form.cleaned_data.get(
                    "account_type"
                )

                seller = None

                if account_type == "seller":

                    selected_plan = form.cleaned_data.get(
                        "selected_plan"
                    )

                    plan = SellerPlan.resolve_plan(
                        selected_plan
                    )

                    seller = Seller.objects.create(
                        user=user,
                        store_name=form.cleaned_data.get(
                            "store_name"
                        ),
                        owner_name=form.cleaned_data.get(
                            "owner_name"
                        ),
                        email=form.cleaned_data.get(
                            "email"
                        ),
                        phone=form.cleaned_data.get(
                            "phone"
                        ),
                        payment_mode=(
                            form.cleaned_data.get(
                                "payment_mode"
                            ) or "cod"
                        ),
                        plan=plan,
                    )

            request.session.pop(
                "pending_email_verification",
                None
            )

            login(request, user)

            if (
                account_type == "seller"
                and form.cleaned_data.get(
                    "selected_plan"
                ) not in (
                    None,
                    "",
                    "free",
                )
            ):
                return redirect(
                    "seller_plan_checkout",
                    slug=seller.slug
                )

            return redirect(
                "seller_dashboard"
                if account_type == "seller"
                else "homepage"
            )

    else:

        form = SignupForm(
            request=request
        )

    return render(
        request,
        "registration/signup.html",
        {
            "form": form
        }
    )