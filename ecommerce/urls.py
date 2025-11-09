from django.urls import path
from . import views
from django.contrib.auth.views import LoginView, LogoutView

urlpatterns = [
    path('', views.home, name='home'),
    path('product/<str:sku>/', views.product_detail, name='product_detail'),
    path('login/', LoginView.as_view(template_name='ecommerce/login.html'), name='login'),
    path('signup/', views.signup, name='signup'),
    path('logout/', LogoutView.as_view(next_page='home'), name='logout'),
    path('loaddata/', views.load_data, name='load_data'),
]