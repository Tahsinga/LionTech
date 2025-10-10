document.addEventListener('DOMContentLoaded', function () {
// Select all forms inside product cards for Add to Cart and the inline details form
const addToCartForms = Array.from(document.querySelectorAll('#productList form'));
const inlineForm = document.querySelector('#product_details_page form[action$="addProduct_to_cart/"]') || document.querySelector('#product_details_page form');
if (inlineForm) addToCartForms.push(inlineForm);

addToCartForms.forEach(form => {
    // Avoid double-binding
    if (form.__addToCartBound) return;
    form.__addToCartBound = true;

    form.addEventListener('submit', function (event) {
        // If the form is a normal submission (no JS), allow it — but prefer AJAX
        event.preventDefault();  // Prevent form from submitting normally

        const url = form.action;
        const formData = new FormData(form);

                // Pre-submit validation: ensure required fields are present and non-empty
                try {
                    const required = ['product_id', 'name', 'price'];
                    const missing = [];
                    for (const key of required) {
                        const val = formData.get(key);
                        if (val === null || val === undefined || String(val).trim() === '') missing.push(key);
                    }
                    if (missing.length) {
                        console.error('add-to-cart blocked: missing required fields:', missing);
                        alert('Cannot add product to cart: missing fields: ' + missing.join(', '));
                        return;
                    }

                    const entries = [];
                    for (const pair of formData.entries()) entries.push(`${pair[0]}=${pair[1]}`);
                    console.debug('add-to-cart submit', url, entries.join('&'));
                } catch (e) {
                    console.warn('validation error', e);
                }

            fetch(url, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: formData
        })
        .then(response => {
            // Try to parse JSON; if server responded with an HTML error page, fall back
            return response.json().catch(() => ({ success: false, message: 'Invalid server response', status: response.status }));
        })
            .then(data => {
                if (data && data.success) {
                    // Refresh cart UI if available
                    if (typeof fetchCartData === 'function') fetchCartData();

                    // Log informational message
                    try {
                        console.info('Added to cart', { product_id: data.product_id, quantity: data.quantity, cart_count: data.cart_count });
                    } catch (e) {}

                    // Show bootstrap toast if present
                    try {
                        const toastEl = document.getElementById('cartSuccessToast');
                        if (toastEl && window.bootstrap && typeof window.bootstrap.Toast === 'function') {
                            // Update message if server provided one
                            const body = toastEl.querySelector('.toast-body');
                            if (body && data.message) body.textContent = data.message;
                            const toast = new window.bootstrap.Toast(toastEl, { delay: 2500 });
                            toast.show();
                        }
                    } catch (e) { console.warn('toast show failed', e); }
                } else {
                    alert('Error: ' + (data.message || 'Failed to add product.'));
                }
            })
        .catch(error => {
                            console.error('add-to-cart failed', error);
                            alert('An error occurred: ' + (error && error.message ? error.message : error));
        });
    });
});
    // Re-bind inline form when product details are loaded dynamically
    try {
        const container = document.getElementById('product_details_page');
        if (container) {
            container.addEventListener('productDetailsLoaded', function () {
                // re-run binding: find the inline form and if not bound, bind it
                const inline = container.querySelector('form[action$="addProduct_to_cart/"]') || container.querySelector('form');
                if (inline && !inline.__addToCartBound) {
                    // push to addToCartForms and bind via the same code path by dispatching a dummy submit listener
                    addToCartForms.push(inline);
                    // emulate same binding logic
                    inline.__addToCartBound = false; // ensure binding occurs
                    // create and dispatch a custom event to trigger binding code above
                    const ev = new Event('DOMContentLoaded');
                    document.dispatchEvent(ev);
                }
            });
        }
    } catch (e) {}
});
