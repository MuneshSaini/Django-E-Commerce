from django.contrib import admin
from .models import Tag, Product, Interaction

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock', 'display_tags') # <-- ADDED 'stock'
    list_filter = ('category',)
    search_fields = ('name', 'tags__name')
    filter_horizontal = ('tags',)
    # ADDED fields for the edit form
    fields = ('name', 'description', 'category', 'price', 'stock', 'tags')

    def display_tags(self, obj):
        return ", ".join([tag.name for tag in obj.tags.all()])
    display_tags.short_description = 'Tags'

@admin.register(Interaction)
class InteractionAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'action', 'rating', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('user__username', 'product__name')
    list_select_related = ('user', 'product')