from django.http import HttpResponse
from .models import ProductDeleteOTP, Products
import random
from django.core.mail import send_mail

def request_delete_product(request, product_id):
    product = Product.objects.get(id=product_id)
    otp = str(random.randint(100000, 999999))
    ProductDeleteOTP.objects.create(user=request.user, product=product, otp=otp)

    send_mail(
        'OTP for Product Deletion',
        f'Your OTP is: {otp}',
        'admin@example.com',
        [request.user.email],
    )

    return render(request, 'enter_otp.html', {'product_id': product_id})


def confirm_delete_product(request, product_id):
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        product = Product.objects.get(id=product_id)

        try:
            # ✅ Get the OTP object for this product (doesn't have to be request.user)
            otp_entry = ProductDeleteOTP.objects.get(product=product)

            # ✅ Check if the OTP is expired
            if otp_entry.is_expired():
                otp_entry.delete()
                return HttpResponse("OTP expired. Please request a new one.")

            if otp_entry.otp != entered_otp:
                return HttpResponse("Invalid OTP.")

            # ✅ Delete the product
            product.delete()
            otp_entry.delete()
            return HttpResponse("Product deleted successfully.")

        except ProductDeleteOTP.DoesNotExist:
            return HttpResponse("No OTP found for this product.")
