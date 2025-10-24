"""
Convenience script to build the Cython extension module.
Usage: python cython_build.py build_ext --inplace
"""
from setuptools import setup, Extension
from Cython.Build import cythonize
import numpy

# Define the extension module
extensions = [
    Extension(
        "shop.recommender.cy_similarity",
        ["shop/recommender/cy_similarity.pyx"],
        include_dirs=[numpy.get_include()],
        extra_compile_args=["-O3"], # Optimization flag
        extra_link_args=[],
    )
]

# Use setuptools to build the extension
setup(
    ext_modules=cythonize(
        extensions,
        compiler_directives={'language_level': "3"},
        annotate=True  # Generates a .html file for analysis
    )
)