//show the quantity at cart icon 
document.addEventListener('DOMContentLoaded', () => {
    const buttons = document.querySelectorAll('.add-to-cart-btn');
    const cartCountSpan = document.getElementById('cart-count');

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

    buttons.forEach(button => {
        button.addEventListener('click', () => {
        const productId = button.getAttribute('data-product-id');

        fetch("{% url 'add_to_cart' %}", {
            method: 'POST',
            headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': '{{ csrf_token }}'
            },
            body: new URLSearchParams({
            'product_id': productId
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
            // ✅ Show custom message
            showTemporaryMessage("✅ Added to cart!");

            // ✅ Update cart count visually
            if (data.cart_count !== undefined) {
                cartCountSpan.textContent = data.cart_count;
            }
            } else {
            showTemporaryMessage("❌ Error: " + data.message);
            }
        })
        .catch(error => {
            showTemporaryMessage("❌ An error occurred.");
            console.error('Error:', error);
        });
        });
    });
});