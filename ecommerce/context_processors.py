from .models import Cart


def cart_context(request):
    """
    Context processor to add cart information to all templates
    """
    cart_count = 0
    cart = None
    
    if hasattr(request, 'user') and request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            cart_count = cart.total_items if cart else 0
        except Cart.DoesNotExist:
            cart = None
            cart_count = 0
        except Exception:
            # Handle any other unexpected errors gracefully
            cart = None
            cart_count = 0
    
    return {
        'cart': cart,
        'cart_count': cart_count,
    }
