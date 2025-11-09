from django.db import models
from django.contrib.auth.models import User

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