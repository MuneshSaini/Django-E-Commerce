import numpy as np

def cosine_similarity_top_k(matrix: np.ndarray, vector: np.ndarray, k: int = 5) -> np.ndarray:
    """
    Pure Python/NumPy implementation of cosine similarity to find top k items.
    
    Args:
        matrix (np.ndarray): The (n_products, n_features) matrix.
        vector (np.ndarray): The (1, n_features) vector to compare against.
        k (int): The number of top similar indices to return.
        
    Returns:
        np.ndarray: An array of the top k most similar row indices from the matrix.
    """
    # Ensure vector is 1D for dot product calculations
    vector_1d = vector.flatten()

    # Calculate dot product
    dot_product = matrix.dot(vector_1d)

    # Calculate norms
    matrix_norms = np.linalg.norm(matrix, axis=1)
    vector_norm = np.linalg.norm(vector_1d)
    
    # Avoid division by zero for products with no tags
    # or if the query vector is all zeros.
    denominator = matrix_norms * vector_norm
    # Create a zero-filled array for similarities
    similarities = np.zeros_like(denominator)
    # Only compute similarity where the denominator is not zero
    valid_indices = denominator > 0
    similarities[valid_indices] = dot_product[valid_indices] / denominator[valid_indices]

    # Get the indices of the top k similarities, in descending order
    # argpartition is faster than argsort for finding top k
    if len(similarities) > k:
        top_k_indices = np.argpartition(similarities, -k)[-k:]
        # Sort only the top k results
        sorted_top_k = top_k_indices[np.argsort(similarities[top_k_indices])][::-1]
    else:
        # If there are fewer items than k, just sort them all
        sorted_top_k = np.argsort(similarities)[::-1]
        
    return sorted_top_k