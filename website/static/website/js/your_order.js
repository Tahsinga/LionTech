let currentSection = 'homeContent'; // Track what's currently visible
const productContainer = document.getElementById('product_details_page') || document.querySelector('.product-container');

function showSection(sectionId) {
    // Hide all sections
    document.getElementById('homeContent').style.display = 'none';
    document.getElementById('cartContents').style.display = 'none';
    document.getElementById('products_addto_cart').style.display = 'none';
    document.getElementById('about_us_page').style.display = 'none';
    document.getElementById('promotion_page').style.display = 'none';
    document.getElementById('accounts_page').style.display = 'none';
    document.getElementById('testimonial_page').style.display = 'none';
    document.getElementById('HistoryContents').style.display = 'none';

    // Always hide product detail container when switching sections
    if (productContainer) {
        productContainer.style.display = 'none';
    }

    // Show the selected section
    const section = document.getElementById(sectionId);
    if (section) {
        section.style.display = 'block';
        // scroll the page so the opened section sits just below the header + category menu
        // use a small timeout so layout settles (helps when elements are inserted/moved)
        setTimeout(() => {
            // Compute visible header height (desktop header or mobile navbar)
            let headerHeight = 0;
            const desktopHeader = document.querySelector('.header-wrapper');
            const mobileHeader = document.querySelector('.mobile-navbar');
            try {
                if (desktopHeader && window.getComputedStyle(desktopHeader).display !== 'none') {
                    headerHeight = desktopHeader.offsetHeight;
                } else if (mobileHeader && window.getComputedStyle(mobileHeader).display !== 'none') {
                    headerHeight = mobileHeader.offsetHeight;
                }
            } catch (e) { /* ignore */ }

            // Account for category menu height if present and not hidden
            let categoryHeight = 0;
            const cat = document.getElementById('categoryMenu');
            try {
                if (cat && window.getComputedStyle(cat).display !== 'none') {
                    categoryHeight = cat.offsetHeight;
                }
            } catch (e) {}

            const rect = section.getBoundingClientRect();
            const top = rect.top + window.pageYOffset - headerHeight - categoryHeight - 8; // small offset
            window.scrollTo({ top: Math.max(0, top), behavior: 'smooth' });
        }, 50);
    }

    // If we're showing the products page, ensure the product grid is visible
    const productList = document.getElementById('productList');
    if (productList) {
        if (sectionId === 'promotion_page') {
            // remove any inline hiding applied by product detail logic
            productList.style.display = ''; 
        }
    }

    // Update tracker
    currentSection = sectionId;
}
// Event listeners for buttons/navigation:

// Show products list when clicking inside #load_product_list
document.getElementById('load_product_list').addEventListener('click', function(e) {
    e.preventDefault();  // Prevent default if it's an anchor
    showSection('promotion_page');
});

document.getElementById('load_testimony').addEventListener('click', function(e) {
    e.preventDefault();  // Prevent default if it's an anchor
    showSection('testimonial_page');
});

document.getElementById('load_accounts').addEventListener('click', function(e) {
    e.preventDefault();  // Prevent default if it's an anchor
    showSection('accounts_page');
});

document.getElementById('load_home_contents').addEventListener('click', function(e) {
    e.preventDefault();  // Prevent default if it's an anchor
    showSection('homeContent');
});

// Show cart add to cart section on cart icon click
document.getElementById('cartIcon').addEventListener('click', function(e) {
    e.preventDefault();
    showSection('products_addto_cart');
});
document.getElementById('load_my_cart').addEventListener('click', function(e) {
    e.preventDefault();
    showSection('products_addto_cart');
});
document.getElementById('toggleViewBtn').addEventListener('click', function(e) {
    e.preventDefault();
    showSection('HistoryContents');
});
document.getElementById('load_about_us').addEventListener('click', function(e) {
    e.preventDefault();
    showSection('about_us_page');
});

// Mirror desktop handlers for mobile-specific controls (if present)
try {
    const cartMobile = document.getElementById('cartIconMobile');
    if (cartMobile) {
        cartMobile.addEventListener('click', function(e) {
            e.preventDefault();
            showSection('products_addto_cart');
        });
    }

    const toggleMobile = document.getElementById('toggleViewBtnMobile');
    if (toggleMobile) {
        toggleMobile.addEventListener('click', function(e) {
            e.preventDefault();
            showSection('HistoryContents');
        });
    }

    // Some mobile layouts may reuse the same id for load_my_cart; ensure it works
    const loadMyCartMobile = document.getElementById('load_my_cart') || document.getElementById('load_my_cart_mobile');
    if (loadMyCartMobile) {
        loadMyCartMobile.addEventListener('click', function(e) {
            e.preventDefault();
            showSection('products_addto_cart');
        });
    }
} catch (e) {
    // If DOM isn't ready or elements are missing, fail silently
}

// On page load, start at homeContent
window.addEventListener('load', function() {
    // If the URL contains product detail path, keep products visible
    const url = new URL(window.location.href);
    const hasQuery = url.searchParams.has('search') || url.searchParams.has('filter') || url.searchParams.has('page');

    if (window.location.pathname.includes('/product/') || hasQuery) {
        showSection('promotion_page');
    } else {
        showSection('homeContent');
    }
});

// Keep category menu visually fixed below the active header by adjusting its top value.
function adjustCategoryMenu() {
    const cat = document.getElementById('categoryMenu');
    if (!cat) return;

    let headerHeight = 0;
    const desktopHeader = document.querySelector('.header-wrapper');
    const mobileHeader = document.querySelector('.mobile-navbar');
    try {
        if (desktopHeader && window.getComputedStyle(desktopHeader).display !== 'none') {
            headerHeight = desktopHeader.offsetHeight;
        } else if (mobileHeader && window.getComputedStyle(mobileHeader).display !== 'none') {
            headerHeight = mobileHeader.offsetHeight;
        }
    } catch (e) { /* ignore */ }

    // Set sticky positioning and top so it stays visible beneath header
    cat.style.position = 'sticky';
    cat.style.top = headerHeight + 'px';
    cat.style.zIndex = '900';
}

// Adjust on load and resize
document.addEventListener('DOMContentLoaded', adjustCategoryMenu);
window.addEventListener('resize', adjustCategoryMenu);