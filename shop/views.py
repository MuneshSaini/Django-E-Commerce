from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from .models import Product, Interaction
from .forms import AddToCartForm, UpdateCartQuantityForm
from .services import Cart
from .recommender.content import similar_products, recommendations_for_user

# ... (product_list, product_detail, etc. are unchanged) ...
def product_list(request):
    products = Product.objects.all().prefetch_related('tags')
    user_recommendations = []
    if request.user.is_authenticated:
        user_recommendations = recommendations_for_user(request.user, k=4)
    return render(request, 'shop/product_list.html', {'products': products, 'user_recommendations': user_recommendations})

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    form = AddToCartForm()
    if request.user.is_authenticated:
        Interaction.objects.update_or_create(user=request.user, product=product, action=Interaction.Action.VIEW)
    similar_items = similar_products(product.id, k=4)
    return render(request, 'shop/product_detail.html', {'product': product, 'form': form, 'similar_items': similar_items})

@require_POST
def add_to_cart(request, product_id):
    """Adds a product to the session-based cart."""
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    form = AddToCartForm(request.POST)

    if form.is_valid():
        quantity = form.cleaned_data['quantity']
        # THE FIX: Add the override_quantity=True argument here.
        cart.add(
            product=product,
            quantity=quantity,
            override_quantity=True 
        )
        return redirect('shop:cart_view')
    
    return redirect('shop:product_detail', pk=product_id)


def remove_from_cart(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    return redirect('shop:cart_view')

def cart_view(request):
    cart = Cart(request)
    return render(request, 'shop/cart.html', {'cart': cart})

@require_POST
def update_cart(request, product_id):
    """Updates the quantity of a product in the cart and returns JSON if AJAX."""
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    form = UpdateCartQuantityForm(request.POST)

    if form.is_valid():
        quantity = form.cleaned_data['quantity']
        cart.add(product, quantity=quantity, override_quantity=True)

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            # Use the iterable version to get total_price for this item
            item_total_price = 0
            for item in cart:
                if item['product'].id == product.id:
                    item_total_price = item['total_price']
                    break

            # THE FIX: Convert Decimal values to float() before creating the JSON response.
            return JsonResponse({
                'status': 'success',
                'cart_total_price': float(cart.get_total_price()),
                'cart_total_items': cart.get_total_items(),
                'item_total_price': float(item_total_price),
            })

    # Fallback for non-AJAX requests
    return redirect('shop:cart_view')


@login_required
def checkout(request):
    cart = Cart(request)
    if not cart: return redirect('shop:product_list')
    if request.method == 'POST':
        user = request.user
        for item in cart:
            product = item['product']
            Interaction.objects.update_or_create(user=user, product=product, action=Interaction.Action.PURCHASE, defaults={'rating': 5})
        cart.clear()
        return render(request, 'shop/checkout.html')
    return redirect('shop:cart_view')

@login_required
@require_POST
def record_feedback(request, pk, action):
    if action not in [Interaction.Action.LIKE]: return HttpResponseBadRequest("Invalid action.")
    product = get_object_or_404(Product, pk=pk)
    interaction, created = Interaction.objects.get_or_create(user=request.user, product=product, action=action, defaults={'rating': 5, 'created_at': timezone.now()})
    if not created: interaction.delete()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success', 'action': action, 'created': not created})
    return redirect('shop:product_detail', pk=pk)