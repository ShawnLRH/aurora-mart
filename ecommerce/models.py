from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import random

class EmailVerification(models.Model):
    email = models.EmailField()
    verification_code = models.CharField(max_length=6)
    user_data = models.JSONField()  # Store signup form data temporarily
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_verified = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if not self.pk:  # Only on creation
            # Set expiration to 15 minutes from now
            self.expires_at = timezone.now() + timedelta(minutes=15)
            # Generate 6-digit code
            if not self.verification_code:
                self.verification_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        super().save(*args, **kwargs)
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def __str__(self):
        return f"Verification for {self.email} - {'Verified' if self.is_verified else 'Pending'}"

class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=20)
    employment_status = models.CharField(max_length=30)
    occupation = models.CharField(max_length=50)
    education = models.CharField(max_length=50)
    household_size = models.PositiveIntegerField()
    has_children = models.BooleanField(default=False)
    monthly_income_sgd = models.DecimalField(max_digits=12, decimal_places=2)
    preferred_category = models.CharField(max_length=40, blank=True)

    def __str__(self):
        if self.user:
            return f"Customer: {self.user.email} (Age: {self.age}, Gender: {self.gender})"
        return f"Customer (Age: {self.age}, Gender: {self.gender})"

class Product(models.Model):
    sku_code = models.CharField(max_length=50, unique=True)
    product_name = models.CharField(max_length=200)
    product_description = models.CharField(max_length=1000)
    product_category = models.CharField(max_length=50)
    product_subcategory = models.CharField(max_length=50)
    quantity_on_hand = models.PositiveIntegerField()
    reorder_quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    product_rating = models.DecimalField(max_digits=3, decimal_places=1)

    def __str__(self):
        return self.product_name


class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart for {self.user.email}"
    
    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())
    
    @property
    def subtotal(self):
        return sum(item.total_price for item in self.items.all())
    
    @property
    def total(self):
        # Can add tax, shipping, etc. here in the future
        return self.subtotal


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('cart', 'product')
    
    def __str__(self):
        return f"{self.quantity}x {self.product.product_name}"
    
    @property
    def total_price(self):
        return self.product.unit_price * self.quantity


class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default='Singapore')
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = 'Addresses'
        ordering = ['-is_default', '-created_at']
    
    def __str__(self):
        return f"{self.full_name} - {self.address_line1}, {self.city}"
    
    def save(self, *args, **kwargs):
        # If this address is set as default, unset other defaults
        if self.is_default:
            Address.objects.filter(user=self.user, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)


class Order(models.Model):
    STATUS_CHOICES = [
        ('ORDER_RECEIVED', 'Order Received'),
        ('ORDER_SENT', 'Order Sent'),
        ('DELIVERED', 'Delivered'),
        ('COMPLETED', 'Completed'),
        ('REFUNDED', 'Refunded'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('CREDIT_CARD', 'Credit Card'),
        ('PAYPAL', 'PayPal'),
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('CASH_ON_DELIVERY', 'Cash on Delivery'),
    ]
    
    order_id = models.CharField(max_length=50, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, related_name='orders')
    
    # Address information
    shipping_full_name = models.CharField(max_length=200)
    shipping_phone = models.CharField(max_length=20)
    shipping_address_line1 = models.CharField(max_length=255)
    shipping_address_line2 = models.CharField(max_length=255, blank=True)
    shipping_city = models.CharField(max_length=100)
    shipping_state = models.CharField(max_length=100)
    shipping_postal_code = models.CharField(max_length=20)
    shipping_country = models.CharField(max_length=100)
    
    # Order details
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    shipping_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ORDER_RECEIVED')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    order_sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    refunded_at = models.DateTimeField(null=True, blank=True)
    
    notes = models.TextField(blank=True)
    refund_reason = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Order {self.order_id} - {self.user.email}"
    
    def save(self, *args, **kwargs):
        if not self.order_id:
            # Generate unique order ID
            import uuid
            from django.utils import timezone
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            unique_id = str(uuid.uuid4())[:8].upper()
            self.order_id = f"ORD-{timestamp}-{unique_id}"
        super().save(*args, **kwargs)
    
    @property
    def item_count(self):
        return sum(item.quantity for item in self.items.all())
    
    def get_status_display_color(self):
        colors = {
            'ORDER_RECEIVED': 'primary',
            'ORDER_SENT': 'info',
            'DELIVERED': 'success',
            'COMPLETED': 'success',
            'REFUNDED': 'warning',
            'CANCELLED': 'danger',
        }
        return colors.get(self.status, 'secondary')


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_sku = models.CharField(max_length=50)
    product_name = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    
    def __str__(self):
        return f"{self.quantity}x {self.product_name}"
    
    @property
    def total_price(self):
        return self.unit_price * self.quantity


# Keep Transaction model for backward compatibility
class Transaction(models.Model):
    transaction_id = models.CharField(max_length=50, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, related_name='transactions')
    transaction_date = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    channel = models.CharField(max_length=20, default='Online')
    
    def __str__(self):
        return f"Transaction {self.transaction_id}"
    
    @property
    def item_count(self):
        return sum(item.quantity for item in self.items.all())


class TransactionItem(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_sku = models.CharField(max_length=50)
    product_name = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    
    def __str__(self):
        return f"{self.quantity}x {self.product_name}"
    
    @property
    def total_price(self):
        return self.unit_price * self.quantity


class SupportTicket(models.Model):
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('RESOLVED', 'Resolved'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='support_tickets', null=True, blank=True)
    name = models.CharField(max_length=200)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    admin_response = models.TextField(blank=True, null=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    responded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='support_responses')
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Ticket #{self.id} - {self.subject}"


class Review(models.Model):
    RATING_CHOICES = [
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(choices=RATING_CHOICES)
    title = models.CharField(max_length=200)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    verified_purchase = models.BooleanField(default=True)  # Always true for our system
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ('product', 'user', 'order')  # One review per product per order
    
    def __str__(self):
        return f"{self.rating}★ - {self.product.product_name} by {self.user.email}"