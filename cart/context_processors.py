# views.py is meant for handling requests and returning responses.

# Django expects context processors to live in a module like context_processors.py and contain functions that return dictionaries to inject into every template.


from .models import Cart

def cart_item_count(request):
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            return {'cart_item_count': cart.items.count()}
        except Cart.DoesNotExist:
            return {'cart_item_count': 0}
    return {'cart_item_count': 0}
