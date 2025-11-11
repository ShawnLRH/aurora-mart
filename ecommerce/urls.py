from django.urls import path
from . import views
from django.contrib.auth.views import LoginView, LogoutView

urlpatterns = [
    path('', views.home, name='home'),
    path('search/', views.search_products, name='search_products'),
    path('product/<str:sku>/', views.product_detail, name='product_detail'),
    path('category/<str:category_name>/', views.category_view, name='category_view'),
    path('login/', LoginView.as_view(template_name='ecommerce/login.html'), name='login'),
    path('signup/', views.signup, name='signup'),
    path('verify-email/<int:verification_id>/', views.verify_email, name='verify_email'),
    path('resend-code/<int:verification_id>/', views.resend_verification_code, name='resend_verification_code'),
    path('logout/', LogoutView.as_view(next_page='home'), name='logout'),
    path('loaddata/', views.load_data, name='load_data'),
    
    # Profile URL
    path('profile/', views.profile, name='profile'),
    
    # Cart URLs
    path('cart/', views.cart_view, name='cart_view'),
    path('cart/add/<str:sku>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),
    
    # Support URL
    path('contact-support/', views.contact_support, name='contact_support'),
    
    # Checkout URLs
    path('checkout/', views.checkout, name='checkout'),
    path('checkout/process/', views.process_checkout, name='process_checkout'),
    path('order/confirmation/<str:order_id>/', views.order_confirmation, name='order_confirmation'),
    path('orders/', views.order_history, name='order_history'),
    path('order/<str:order_id>/', views.order_detail, name='order_detail'),
    path('order/<str:order_id>/reorder/', views.reorder, name='reorder'),
    path('order/<str:order_id>/complete/', views.complete_order, name='complete_order'),
    path('order/<str:order_id>/refund/', views.refund_order, name='refund_order'),
]