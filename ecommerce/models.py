from django.db import models

class Customer(models.Model):
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=20)
    employment_status = models.CharField(max_length=30)
    occupation = models.CharField(max_length=50)
    education = models.CharField(max_length=50)
    household_size = models.PositiveIntegerField()
    has_children = models.BooleanField(default=False)
    monthly_income_sgd = models.DecimalField(max_digits=12, decimal_places=2)
    preferred_category = models.CharField(max_length=40)

    def __str__(self):
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