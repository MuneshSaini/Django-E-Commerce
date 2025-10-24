import pandas as pd
import numpy as np
from django.core.cache import cache
from shop.models import Product, Tag, Interaction

# --- Try to import the compiled Cython module, with a fallback to pure Python ---
try:
    from .cy_similarity import cosine_similarity_top_k
    print("INFO: Cython `cy_similarity` module loaded successfully.")
    SIMILARITY_FUNCTION = cosine_similarity_top_k
except ImportError:
    from .py_similarity import cosine_similarity_top_k
    print("WARNING: Could not load Cython module. Falling back to pure Python `py_similarity`.")
    SIMILARITY_FUNCTION = cosine_similarity_top_k


def get_product_tag_matrix():
    """
    Builds and caches a binary product-tag matrix.
    Rows are product IDs, columns are tag IDs.
    """
    matrix = cache.get('product_tag_matrix')
    product_map = cache.get('product_map') # Maps matrix index to product ID
    if matrix is not None and product_map is not None:
        return matrix, product_map

    products = Product.objects.all().prefetch_related('tags')
    tags = Tag.objects.all()

    if not products or not tags:
        return np.array([]), {}

    # Create mapping from ID to matrix index
    product_map = {p.id: i for i, p in enumerate(products)}
    tag_map = {t.id: i for i, t in enumerate(tags)}

    # Initialize a zero matrix
    matrix = np.zeros((len(products), len(tags)), dtype=np.int8)

    # Populate the matrix
    for prod_idx, product in enumerate(products):
        for tag in product.tags.all():
            tag_idx = tag_map[tag.id]
            matrix[prod_idx, tag_idx] = 1

    cache.set('product_tag_matrix', matrix, timeout=3600)  # Cache for 1 hour
    cache.set('product_map', product_map, timeout=3600)
    
    return matrix, product_map


def similar_products(product_id: int, k: int = 5):
    """
    Finds the top k most similar products to a given product.
    
    Args:
        product_id (int): The ID of the product to find similar items for.
        k (int): The number of similar products to return.
        
    Returns:
        A Django QuerySet of Product objects.
    """
    matrix, product_map = get_product_tag_matrix()

    if not product_map or product_id not in product_map:
        return Product.objects.none()

    # Get the index for the given product_id
    product_idx = product_map.get(product_id)
    if product_idx is None:
        return Product.objects.none()
        
    # Get the target vector for the product
    target_vector = matrix[product_idx, :].reshape(1, -1)
    
    # Compute similarity against all other products
    # We ask for k+1 because the most similar item will be the product itself.
    similar_indices = SIMILARITY_FUNCTION(matrix, target_vector, k=k + 1)
    
    # Get the product IDs from the matrix indices, excluding the first one (itself)
    inverse_product_map = {v: k for k, v in product_map.items()}
    similar_product_ids = [inverse_product_map[i] for i in similar_indices if i != product_idx][:k]

    return Product.objects.filter(id__in=similar_product_ids)


def recommendations_for_user(user, k: int = 5):
    """
    Generates personalized product recommendations for a logged-in user.
    It builds a user preference vector based on liked/purchased items.
    """
    matrix, product_map = get_product_tag_matrix()

    if matrix.size == 0 or not product_map:
        return Product.objects.none()

    # Get all products the user has liked or purchased
    positive_interactions = Interaction.objects.filter(
        user=user,
        action__in=[Interaction.Action.LIKE, Interaction.Action.PURCHASE]
    ).select_related('product')

    positive_interacted_pids = [i.product_id for i in positive_interactions]
    if not positive_interacted_pids:
        return Product.objects.none()# No positive interactions, no recommendations

    # Build user preference vector by summing tag vectors of liked/purchased items
    user_preference_vector = np.zeros(matrix.shape[1], dtype=np.int8)
    for pid in positive_interacted_pids:
        if pid in product_map:
            product_idx = product_map[pid]
            user_preference_vector += matrix[product_idx, :]
    
    # Normalize to a binary vector
    user_preference_vector = (user_preference_vector > 0).astype(np.int8).reshape(1, -1)

    # Find items similar to the user's aggregated preference
    similar_indices = SIMILARITY_FUNCTION(matrix, user_preference_vector, k=k + len(positive_interacted_pids))

    # Exclude items the user has already interacted with
    inverse_product_map = {v: k for k, v in product_map.items()}
    all_interacted_pids = set(Interaction.objects.filter(user=user).values_list('product_id', flat=True))

    recommended_ids = []
    for idx in similar_indices:
        pid = inverse_product_map.get(idx)
        if pid and pid not in all_interacted_pids:
            recommended_ids.append(pid)
        if len(recommended_ids) >= k:
            break

    return Product.objects.filter(id__in=recommended_ids)