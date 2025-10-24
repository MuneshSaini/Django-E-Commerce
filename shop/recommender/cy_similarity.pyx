# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# cython: cdivision=True
# cython: initializedcheck=False

import numpy as np
cimport numpy as np
from libc.math cimport sqrt

# Define the data types for arrays
ctypedef np.int8_t DTYPE_t
ctypedef np.float64_t FLOAT_t

def cosine_similarity_top_k(
    np.ndarray[DTYPE_t, ndim=2] matrix,
    np.ndarray[DTYPE_t, ndim=2] vector,
    int k=5
):
    """
    Cython-optimized cosine similarity calculation to find top k items.
    
    This function computes the cosine similarity between a query vector and all
    rows of a matrix, returning the indices of the top k most similar rows.
    """
    # --- Variable Declarations ---
    cdef int n_products = matrix.shape[0]
    cdef int n_features = matrix.shape[1]
    
    # Arrays for results
    cdef np.ndarray[FLOAT_t, ndim=1] similarities = np.zeros(n_products, dtype=np.float64)
    
    # Loop variables
    cdef int i, j
    
    # Calculation variables
    cdef double dot_product
    cdef double matrix_norm_sq, vector_norm_sq
    cdef double matrix_norm, vector_norm
    cdef double sim

    # --- Pre-calculate the norm of the input vector ---
    vector_norm_sq = 0.0
    for j in range(n_features):
        vector_norm_sq += vector[0, j] * vector[0, j]
    vector_norm = sqrt(vector_norm_sq)

    # If the vector norm is zero, all similarities will be zero, so we can exit early.
    if vector_norm == 0.0:
        return np.array([], dtype=np.int32)

    # --- Main Loop: Iterate over each product in the matrix ---
    for i in range(n_products):
        dot_product = 0.0
        matrix_norm_sq = 0.0

        # Calculate dot product and matrix row norm simultaneously
        for j in range(n_features):
            dot_product += matrix[i, j] * vector[0, j]
            matrix_norm_sq += matrix[i, j] * matrix[i, j]
        
        matrix_norm = sqrt(matrix_norm_sq)

        # Calculate cosine similarity and store it
        if matrix_norm > 0.0:
            sim = dot_product / (matrix_norm * vector_norm)
            similarities[i] = sim
        else:
            similarities[i] = 0.0

    # --- Find Top K using NumPy ---
    # Using argpartition is more efficient than a full sort for finding the top k elements.
    if n_products > k:
        top_k_indices = np.argpartition(similarities, -k)[-k:]
        # Sort only the top k results to get them in the correct descending order
        sorted_top_k = top_k_indices[np.argsort(similarities[top_k_indices])][::-1]
    else:
        # If there are fewer items than k, sort all of them
        sorted_top_k = np.argsort(similarities)[::-1]
        
    return sorted_top_k