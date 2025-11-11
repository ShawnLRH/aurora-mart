from django.contrib import admin
from .models import Customer, Product, Order, OrderItem, Address
from django.utils import timezone


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'product_sku', 'product_name', 'quantity', 'unit_price', 'total_price')
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'user', 'status', 'total_amount', 'payment_method', 'created_at')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('order_id', 'user__email', 'user__username', 'shipping_full_name')
    readonly_fields = ('order_id', 'user', 'customer', 'created_at', 'updated_at', 'subtotal', 'shipping_fee', 'tax', 'total_amount')
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_id', 'user', 'customer', 'created_at', 'updated_at', 'status')
        }),
        ('Shipping Details', {
            'fields': ('shipping_full_name', 'shipping_phone', 'shipping_address_line1', 'shipping_address_line2', 
                      'shipping_city', 'shipping_state', 'shipping_postal_code', 'shipping_country')
        }),
        ('Payment & Pricing', {
            'fields': ('payment_method', 'subtotal', 'shipping_fee', 'tax', 'total_amount')
        }),
        ('Status Tracking', {
            'fields': ('order_sent_at', 'delivered_at')
        }),
        ('Additional Info', {
            'fields': ('notes',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Update timestamps when status changes"""
        if change:  # Only for existing orders
            old_obj = Order.objects.get(pk=obj.pk)
            
            # If status changed to ORDER_SENT, set order_sent_at
            if old_obj.status != 'ORDER_SENT' and obj.status == 'ORDER_SENT':
                if not obj.order_sent_at:
                    obj.order_sent_at = timezone.now()
            
            # If status changed to DELIVERED, set delivered_at
            if old_obj.status != 'DELIVERED' and obj.status == 'DELIVERED':
                if not obj.delivered_at:
                    obj.delivered_at = timezone.now()
        
        super().save_model(request, obj, form, change)


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'user', 'city', 'state', 'country', 'is_default', 'created_at')
    list_filter = ('is_default', 'country', 'state')
    search_fields = ('full_name', 'user__email', 'address_line1', 'city', 'postal_code')
    readonly_fields = ('created_at',)


admin.site.register(Customer)
admin.site.register(Product)