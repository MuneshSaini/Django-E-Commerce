from django import forms

class AddToCartForm(forms.Form):
    """Form for validating the quantity when adding a product to the cart."""
    quantity = forms.IntegerField(
        min_value=1, 
        initial=1, 
        widget=forms.NumberInput(attrs={'class': 'quantity-input'})
    )

class UpdateCartQuantityForm(forms.Form):
    """Form for updating the quantity of a product in the cart."""
    quantity = forms.IntegerField(min_value=1)