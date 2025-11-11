from django.urls import path
from . import views

urlpatterns = [
    path('', views.admin_dashboard, name='admin_dashboard'),
    path('products/', views.product_list, name='admin_product_list'),
    path('products/create/', views.product_create, name='admin_product_create'),
    path('products/edit/<str:sku>/', views.product_edit, name='admin_product_edit'),
    path('products/delete/<str:sku>/', views.product_delete, name='admin_product_delete'),
    path('products/stock/<str:sku>/', views.stock_adjust, name='admin_stock_adjust'),
    path('products/import/', views.product_import_csv, name='admin_product_import'),
    path('products/export/', views.product_export_csv, name='admin_product_export'),
    path('products/bulk-price-update/', views.bulk_price_update, name='admin_bulk_price_update'),
    path('alerts/low-stock/', views.low_stock_alerts, name='admin_low_stock_alerts'),
    path('customers/', views.customer_list, name='admin_customer_list'),
    path('customers/edit/<int:customer_id>/', views.customer_edit, name='admin_customer_edit'),
    path('customers/delete/<int:customer_id>/', views.customer_delete, name='admin_customer_delete'),
    path('staff/', views.staff_list, name='admin_staff_list'),
    path('staff/create/', views.staff_create, name='admin_staff_create'),
    path('staff/delete/<int:user_id>/', views.staff_delete, name='admin_staff_delete'),
    path('logs/', views.system_logs, name='admin_system_logs'),
    path('support/', views.support_tickets, name='admin_support_tickets'),
    path('support/<int:ticket_id>/', views.support_ticket_detail, name='admin_support_ticket_detail'),
    path('ai/insights/', views.ai_insights, name='admin_ai_insights'),
    path('ai/rules/', views.association_rules, name='admin_association_rules'),
    path('orders/', views.order_list, name='admin_order_list'),
    path('orders/<str:order_id>/', views.order_detail_admin, name='admin_order_detail'),
]
