from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Tag(models.Model):
    """Represents a product tag."""
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    """Represents a product in the e-commerce store."""
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    tags = models.ManyToManyField(Tag, related_name='products')
    description = models.TextField(blank=True, null=True)
    stock = models.PositiveIntegerField(default=10) # Using PositiveIntegerField for stock
    image = models.ImageField(upload_to='products/', blank=True, null=True)

    def __str__(self):
        return self.name


class Interaction(models.Model):
    """
    Records user interactions with products (view, like, purchase).
    """
    class Action(models.TextChoices):
        VIEW = 'view', 'View'
        LIKE = 'like', 'Like'
        PURCHASE = 'purchase', 'Purchase'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='interactions')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='interactions')
    action = models.CharField(max_length=10, choices=Action.choices)
    rating = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['user', 'product', 'action'], name='unique_user_product_action')
        ]

    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.product.name}"