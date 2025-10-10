document.addEventListener('DOMContentLoaded', () => {
    const buttons = document.querySelectorAll('.add-to-cart-btn');
    const cartCountSpan = document.getElementById('cart-count');
    const addToCartModal = new bootstrap.Modal(document.getElementById('addToCartModal'));
    
    // Cart functionality
    let cart = JSON.parse(localStorage.getItem('cart')) || [];
    
    function showTemporaryMessage(message) {
        const msg = document.createElement('div');
        msg.className = 'position-fixed top-0 start-50 translate-middle-x mt-3 alert alert-success text-center shadow';
        msg.style.zIndex = '1050';
        msg.innerText = message;
        document.body.appendChild(msg);
        
        setTimeout(() => {
            msg.remove();
        }, 2000);
    }
    
    function updateCartCount() {
        const count = cart.reduce((total, item) => total + item.quantity, 0);
        cartCountSpan.textContent = count;
        localStorage.setItem('cart', JSON.stringify(cart));
    }
    
    function calculatePrices() {
        const quantity = parseInt(document.getElementById('quantityInput').value);
        const price = parseFloat(document.getElementById('cartPopupPrice').textContent.replace('$', ''));
        const subtotal = (price * quantity).toFixed(2);
        const total = (parseFloat(subtotal) + 5.00).toFixed(2);
        
        document.getElementById('subtotalPrice').textContent = `$${subtotal}`;
        document.getElementById('totalPrice').textContent = `$${total}`;
    }
    
    // Quantity controls
    document.getElementById('incrementQty').addEventListener('click', () => {
        const input = document.getElementById('quantityInput');
        input.value = parseInt(input.value) + 1;
        calculatePrices();
    });
    
    document.getElementById('decrementQty').addEventListener('click', () => {
        const input = document.getElementById('quantityInput');
        if (parseInt(input.value) > 1) {
            input.value = parseInt(input.value) - 1;
            calculatePrices();
        }
    });
    
    document.getElementById('quantityInput').addEventListener('change', calculatePrices);
    
    // Proceed to checkout button
    document.getElementById('proceedToCheckout').addEventListener('click', () => {
        const form = document.getElementById('shippingForm');
        if (!form.checkValidity()) {
            form.classList.add('was-validated');
            return;
        }
        
        // Here you would typically submit the order to your backend
        alert('Order submitted successfully!');
        addToCartModal.hide();
    });
    
    buttons.forEach(button => {
        button.addEventListener('click', (e) => {
            const productCard = e.target.closest('.product-card');
            const productId = button.getAttribute('data-product-id');
            const productName = productCard.querySelector('.product-name').textContent;
            const productPrice = productCard.querySelector('.text-success').textContent;
            const productCategory = productCard.querySelectorAll('.text-muted small')[1].textContent.replace('Category: ', '');
            const productImage = productCard.querySelector('img').src;
            
            // Check if product already in cart
            const existingItem = cart.find(item => item.id === productId);
            
            if (existingItem) {
                existingItem.quantity += 1;
            } else {
                cart.push({
                    id: productId,
                    name: productName,
                    price: parseFloat(productPrice.replace('$', '')),
                    category: productCategory,
                    image: productImage,
                    quantity: 1
                });
            }
            
            // Update cart in localStorage
            localStorage.setItem('cart', JSON.stringify(cart));
            
            // Update UI
            updateCartCount();
            
            // Populate and show the add to cart modal
            document.getElementById('cartPopupImage').src = productImage;
            document.getElementById('cartPopupName').textContent = productName;
            document.getElementById('cartPopupPrice').textContent = productPrice;
            document.getElementById('cartPopupCategory').textContent = productCategory;
            document.getElementById('quantityInput').value = existingItem ? existingItem.quantity : 1;
            calculatePrices();
            
            // Show the modal
            addToCartModal.show();
            
            // Show success message
            showTemporaryMessage("✅ Added to cart!");
        });
    });
    
    // Initialize cart count on page load
    updateCartCount();
});