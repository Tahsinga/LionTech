document.addEventListener("DOMContentLoaded", function () {
  const searchInput = document.getElementById('liveSearchInput');
  const searchInputMobile = document.getElementById('liveSearchInputMobile');
  const productList = document.getElementById('productList');
  const paginationNav = document.getElementById('productPagination');
  const liveProducts = {}; // keep rendered products by id for actions (add to cart)

  // helper to build product card markup matching server template
  function buildProductCard(product) {
    const pid = product.id || product.pk || '';
    const carouselId = `productCarousel_live_${pid}`;
    // collect images (API may provide full URLs)
    const imgs = [product.image, product.image_2, product.image_3, product.image_4].filter(Boolean);

    const carouselInner = imgs.length ? imgs.map((src, idx) => `\n              <div class="carousel-item ${idx === 0 ? 'active' : ''}">\n                <a href="/product/${pid}/">\n                  <img src="${src}" class="d-block w-100 img-fluid rounded clickable-image" alt="${product.name || ''}" data-product-id="${pid}">\n                </a>\n              </div>`).join('') : `\n              <div class="carousel-item active">\n                <a href="/product/${pid}/">\n                  <img src="/static/website/images/default-image.svg" class="d-block w-100 img-fluid rounded clickable-image" alt="${product.name || ''}" data-product-id="${pid}">\n                </a>\n              </div>`;

    return `
      <div class="col-md-4 mb-4 product-item" data-category="${product.category || ''}">
        <div class="product-card">
          <div class="product-image-wrapper text-center mb-3">
            <div id="${carouselId}" class="carousel slide" data-bs-ride="carousel">
              <div class="carousel-inner">${carouselInner}
              </div>
              <button class="carousel-control-prev" type="button" data-bs-target="#${carouselId}" data-bs-slide="prev">
                <span class="carousel-control-prev-icon" aria-hidden="true"></span>
                <span class="visually-hidden">Previous</span>
              </button>
              <button class="carousel-control-next" type="button" data-bs-target="#${carouselId}" data-bs-slide="next">
                <span class="carousel-control-next-icon" aria-hidden="true"></span>
                <span class="visually-hidden">Next</span>
              </button>
            </div>
          </div>

          <div class="product-details text-center mb-2">
            <h5 class="product-name">${product.name || ''}</h5>
            <p class="product-price">$${product.price || ''}</p>
            <p class="product-meta"><strong>Condition:</strong> ${product.condition || ''}</p>
          </div>

          <div class="text-center mt-auto">
            <div class="text-center mt-auto">
              ${product.location === 'local' ? `<p class="product-meta">Delivery: <strong>Tommorrow</strong></p>` : product.location === 'exotic' ? `<p class="product-meta">Delivery: <strong>2 Weeks</strong></p>` : `<p class="product-meta">Delivery: <strong>Standard delivery</strong></p>`}
            </div>
            <div class="stars">★★★★★</div>
          </div>

          <div class="text-center mt-3">
            <button class="btn btn-success w-100 add-to-cart-btn" style="background: #2E6591;" type="button" onclick="addToCartById(${pid})">
              <i class="bi bi-cart-plus me-1"></i> Add to Cart
            </button>
          </div>
        </div>
      </div>
    `;
  }

  // Unified handler for live search input (desktop + mobile)
  let searchDebounceTimer = null;
  function handleLiveSearchInput(e) {
    const query = (e.target.value || '').trim();

    // Ensure product view is shown when user starts typing
    if (typeof showSection === 'function') showSection('promotion_page');

    // debounce requests to reduce load
    if (searchDebounceTimer) clearTimeout(searchDebounceTimer);
    searchDebounceTimer = setTimeout(() => {
      fetch(`/live-search-products/?search=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
          productList.innerHTML = '';
          // when performing live search, hide server pagination
          if (paginationNav) paginationNav.style.display = 'none';

          if (!data || data.length === 0) {
            productList.innerHTML = '<p>No products found.</p>';
            return;
          }

          data.forEach(product => {
            const pid = product.id || product.pk || '';
            liveProducts[pid] = product;
            productList.innerHTML += buildProductCard(product);
          });
        })
        .catch(err => console.error('Live search error', err));
    }, 200);
  }

  if (searchInput) searchInput.addEventListener('input', handleLiveSearchInput);
  if (searchInputMobile) searchInputMobile.addEventListener('input', handleLiveSearchInput);

  // Handle category clicks with AJAX (no page reload). Bind both explicit ajax-category
  // buttons and standard category-link anchors rendered in the sidebar.
  document.querySelectorAll('.ajax-category, .category-link').forEach(link => {
    link.addEventListener('click', function(e) {
      // Always prevent default navigation so we can fetch via AJAX
      e.preventDefault();

      // Prefer data-filter attribute, fall back to parsing href query param
      let filter = this.getAttribute('data-filter') || '';
      if (!filter) {
        try {
          const url = new URL(this.href, window.location.origin);
          filter = url.searchParams.get('filter') || '';
        } catch (err) { /* ignore */ }
      }

      const search = searchInput ? searchInput.value.trim() : '';

      // show products section via global showSection if available
      if (typeof showSection === 'function') showSection('promotion_page');

      // Build API URL - use get_products endpoint which is paginated
      const apiUrl = `/api/products/?page=1&search=${encodeURIComponent(search)}&filter=${encodeURIComponent(filter)}`;

      fetch(apiUrl)
        .then(res => res.json())
        .then(json => {
          const items = json.results || json;
          productList.innerHTML = '';

          if (!items || items.length === 0) {
            productList.innerHTML = '<div class="col-12 text-center py-5"><i class="bi bi-exclamation-circle fs-1 text-muted"></i><p class="fs-4 text-muted">No products found.</p></div>';
            return;
          }

          // Render items using shared builder to match server markup
          items.forEach(product => {
            const pid = product.id || product.pk || '';
            liveProducts[pid] = product;
            productList.innerHTML += buildProductCard(product);
          });

          // Hide original server pagination while showing AJAX results
          if (paginationNav) paginationNav.style.display = 'none';
        })
        .catch(err => console.error('Category fetch error', err));
    });
  });

  // Helper: get CSRF cookie (same helper used in other scripts)
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let cookie of cookies) {
        cookie = cookie.trim();
        if (cookie.startsWith(name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  // Add to cart by product id using server endpoint addProduct_to_cart/
  window.addToCartById = function(pid) {
    const prod = liveProducts[pid];
    if (!prod) {
      console.error('Product data not available for', pid);
      return;
    }

    const url = '/addProduct_to_cart/';
    const formData = new FormData();
    formData.append('product_id', pid);
    formData.append('name', prod.name || '');
    formData.append('price', prod.price || '0');
    formData.append('condition', prod.condition || '');
    formData.append('category', prod.category || '');
    formData.append('image_url', prod.image || '');

    fetch(url, {
      method: 'POST',
      headers: {
        'X-CSRFToken': getCookie('csrftoken')
      },
      body: formData
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
        // update cart badge if provided
        try {
          const badge = document.getElementById('cart-count');
          const badgeMobile = document.getElementById('cart-count-mobile');
          if (data.cart_count !== undefined) {
            if (badge) {
              badge.textContent = data.cart_count;
              badge.style.display = data.cart_count && data.cart_count > 0 ? 'inline-block' : 'none';
            }
            if (badgeMobile) {
              badgeMobile.textContent = data.cart_count;
              badgeMobile.style.display = data.cart_count && data.cart_count > 0 ? 'inline-block' : 'none';
            }
          }
        } catch (e) {}
      } else {
        alert(data.message || 'Failed to add to cart');
      }
    })
    .catch(err => {
      console.error('Add to cart error', err);
      alert('Failed to add to cart.');
    });
  };
});
