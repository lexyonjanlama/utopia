from django.shortcuts import render, get_object_or_404, redirect
from .models import CartItem, Product, Category, Cart, Order, OrderItem, Size, Wishlist,UserProfile,Review, ContactMessage
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.urls import reverse
from .forms import UserRegistrationForm, UserLoginForm, CheckoutForm, ContactForm, UserProfileForm,ReviewForm
from django.contrib import messages
from django.core.paginator import Paginator
# Home View
def home(request):
    featured_products = Product.objects.filter(featured=True)  
    return render(request, 'store/home.html', {'featured_products': featured_products})

# Shop (Product List) View
def shop(request):
    categories = Category.objects.all()
    sizes = Size.objects.all() 
    selected_category = request.GET.get('category')
    selected_size = request.GET.get('size')
    search_query = request.GET.get('q', '') 

    products = Product.objects.all()
    
    # Filter by category, size, or search query
    if selected_category:
        products = products.filter(category__id=selected_category)
    
    if selected_size:
        products = products.filter(sizes__id=selected_size)

    if search_query:
        products = products.filter(name__icontains=search_query)

    # Pagination logic
    paginator = Paginator(products, 12)  
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'store/shop.html', {
        'categories': categories,
        'sizes': sizes,
        'products': page_obj,  # Pass the paginated products to the template
        'selected_category': selected_category,
        'selected_size': selected_size,
        'query': search_query,
    })




# Product Detail View
def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    sizes = Size.objects.all() 
    reviews = Review.objects.filter(product=product)  
    
    user_reviewed = Review.objects.filter(user=request.user, product=product).exists()

    if request.method == 'POST' and request.user.is_authenticated and not user_reviewed:
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            if 1 <= review.rating <= 5:
                review.save()
                messages.success(request, 'Your review has been submitted.')
                return redirect('product_detail', product_id=product.id)
            else:
                messages.error(request, 'Please provide a rating between 1 and 5.')
        else:
            messages.error(request, 'Invalid review form data.')
    else:
        form = ReviewForm()

    return render(request, 'store/product_detail.html', {
        'product': product,
        'sizes': sizes,
        'reviews': reviews,
        'form': form,  
    })

# Checkout View
@login_required
def checkout(request):
    cart_items = Cart.objects.filter(user=request.user)
    total_price = sum(item.product.price * item.quantity for item in cart_items)
    context = {
        'cart_items': cart_items,
        'total_price': total_price
    }
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = Order.objects.create(user=request.user, total_price=total_price, status='Pending')
            for item in cart_items:
                OrderItem.objects.create(order=order, product=item.product, quantity=item.quantity)

            cart_items.delete()
            return redirect('order_success', order_id=order.id)  
    else:
        form = CheckoutForm()

    return render(request, 'store/checkout.html', {'cart_items': cart_items, 'total_price': total_price, 'form': form})

# Place Order View
@login_required
def place_order(request):
    cart_items = Cart.objects.filter(user=request.user)

    if not cart_items.exists():
        return render(request, 'store/view_cart.html', {
            'message': 'Your cart is empty. Please add items to your cart before placing an order.'
        })

    total_price = sum(item.product.price * item.quantity for item in cart_items)

    order = Order.objects.create(user=request.user, total_price=total_price, status='Pending')

    for item in cart_items:
        OrderItem.objects.create(
            order=order,
            product=item.product,
            quantity=item.quantity,
            price=item.product.price
        )

    # Now delete items from Cart model
    cart_items.delete()

    return redirect('order_success', order_id=order.id)


# Order Success View
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'store/order_success.html', {'order': order})

# Register View
def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('shop')  
    else:
        form = UserRegistrationForm()
    return render(request, 'store/register.html', {'form': form})

# Login View
def user_login(request):
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        
        if form.is_valid():  
            username = form.cleaned_data['username']  
            password = form.cleaned_data['password']  
            
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)  
                return redirect('home')  
            else:
                form.add_error(None, 'Invalid username or password')
        else:
            form.add_error(None, 'Form is not valid')
    else:
        form = UserLoginForm()      
    return render(request, 'store/login.html', {'form': form})

# Logout View
def user_logout(request):
    logout(request)
    return redirect('shop')  

# Search View
def search(request):
    query = request.GET.get('q', '')
    products = Product.objects.filter(name__icontains=query)  
    return render(request, 'store/search.html', {'products': products, 'query': query})

# Filter Products View
def filter_products(request):
    category = request.GET.get('category', None)
    size = request.GET.get('size', None)
    products = Product.objects.all()

    if category:
        products = products.filter(category__name=category)
    if size:
        products = products.filter(sizes__name=size)

    return render(request, 'store/shop.html', {'products': products})

# Add to Cart View
@login_required
def add_to_cart(request, product_id):
    product = Product.objects.get(id=product_id)
    size_id = request.POST.get('size')
    size = get_object_or_404(Size, id=size_id)
    quantity = int(request.POST.get('quantity', 1))

    cart_item, created = Cart.objects.get_or_create(
        user=request.user,
        product=product,
        size=size,
        defaults={'quantity': quantity},
    )

    if not created:
        cart_item.quantity += quantity
        cart_item.save()

    return redirect('cart')

# View Cart View
@login_required
def view_cart(request):
    cart_items = Cart.objects.filter(user=request.user)
    return render(request, 'store/view_cart.html', {'cart_items': cart_items})

# Remove from Cart View
@login_required
def remove_from_cart(request, cart_id):
    cart_item = Cart.objects.filter(user=request.user, id=cart_id).first()

    if cart_item:
        cart_item.delete()
        messages.success(request, "Item removed from cart.")
    else:
        messages.error(request, "Item not found in cart.")
    
    return redirect('view_cart')  

# Add to Wishlist View
@login_required
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    return redirect('wishlist')

# View Wishlist View
@login_required
def view_wishlist(request):
    wishlist_items = Wishlist.objects.filter(user=request.user)
    return render(request, 'store/view_wishlist.html', {'wishlist_items': wishlist_items})

# Remove from Wishlist View
@login_required
def remove_from_wishlist(request, product_id):
    wishlist_item = get_object_or_404(Wishlist, user=request.user, product_id=product_id)
    wishlist_item.delete()  
    return HttpResponseRedirect(reverse('view_wishlist'))

# Static Pages Views
def about(request):
    return render(request, 'store/about.html')

def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            messages.success(request, 'Your message has been sent successfully.')
            return redirect('contact')
    else:
        form = ContactForm()
    return render(request, 'store/contact.html', {'form': form})

#Profile View
@login_required
def profile_view(request):
    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)

    return render(request, 'store/profile.html', {'profile': profile})

# Edit Profile View
@login_required
def edit_profile(request):
    profile = UserProfile.objects.get(user=request.user)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('profile')  
    else:
        form = UserProfileForm(instance=profile)
    
    return render(request, 'store/edit_profile.html', {'form': form})

# View for Order History
@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'store/order_history.html', {'orders': orders})

# Order Detail View
@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = OrderItem.objects.filter(order=order)
    return render(request, 'store/order_detail.html', {'order': order, 'order_items': order_items})

def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            message = form.cleaned_data['message']

            ContactMessage.objects.create(name=name, email=email, message=message)
            
            messages.success(request, 'Your message has been sent successfully.')
            return redirect('contact')
    else:
        form = ContactForm()
    return render(request, 'store/contact.html', {'form': form})