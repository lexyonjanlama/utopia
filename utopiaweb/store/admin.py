from django.contrib import admin
from .models import Category, Size, Product, UserProfile, Cart, Wishlist, Order, OrderItem, Review, CartItem,ContactMessage

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ('product', 'quantity', 'price')

class OrderAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_price', 'status', 'created_at')
    search_fields = ('user__username',)
    list_filter = ('status',)
    inlines = [OrderItemInline]
    readonly_fields = ('user', 'total_price', 'status', 'created_at')


admin.site.register(Category)
admin.site.register(Size)
admin.site.register(Product)
admin.site.register(UserProfile)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Wishlist)
admin.site.register(Order, OrderAdmin)
admin.site.register(Review)
admin.site.register(ContactMessage)

