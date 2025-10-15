// Fresh, single-purpose handler for opening `#product_details_page`
// when an element with class `clickable-image` is clicked.

document.addEventListener('DOMContentLoaded', function () {
  const container = document.getElementById('product_details_page');
  const header = document.querySelector('.header-wrapper');

  // Sections that make up the main app UI. When showing product details
  // we hide these and restore the previously visible one on close.
  const MAIN_SECTIONS = ['homeContent','promotion_page','products_addto_cart','cartContents','HistoryContents','accounts_page','testimonial_page'];
  let previousVisibleSection = null;

  if (!container) return; // Exit if details container not found

  // Safely set inner text for a selector inside the container
  // Determine whether a value is meaningful (not an NA/placeholder)
  function isMeaningful(val) {
    if (val === null || val === undefined) return false;
    try {
      const s = String(val).trim();
      if (!s) return false;
      const low = s.toLowerCase();
      const bad = new Set(['na', 'n/a', 'none', 'null', '-', 'n.a.', 'n.a', 'unknown', 'n/a (not applicable)', 'n/a (na)']);
      return !bad.has(low);
    } catch (e) { return false; }
  }

  function setText(selector, text, label) {
    // If text isn't meaningful, remove/hide any existing element and don't create a row.
    if (!isMeaningful(text)) {
      const existing = container.querySelector(selector);
      if (existing) {
        // if it's inside a .detail-item wrapper, remove the wrapper entirely
        const wrap = existing.closest('.detail-item');
        if (wrap && wrap.parentNode) wrap.parentNode.removeChild(wrap);
        else existing.textContent = '';
      }
      return;
    }

    const el = container.querySelector(selector);
    if (el) {
      el.textContent = String(text);
      return;
    }

    // Create a detail row because we have meaningful text
    try {
      const detailsWrap = container.querySelector('.details-container');
      if (!detailsWrap) return;
      const key = selector.replace(/^[.#]/, '');
      const wrapper = document.createElement('div');
      wrapper.className = 'detail-item mb-2';
      const labelText = label || key.split('-').map(s => s.charAt(0).toUpperCase() + s.slice(1)).join(' ');
      wrapper.innerHTML = `<strong>${labelText}:</strong> <span class="${key}"></span>`;
      detailsWrap.appendChild(wrapper);
      const span = wrapper.querySelector('.' + key);
      if (span) span.textContent = String(text);
    } catch (e) {
      // ignore DOM creation errors
    }
  }

  // Populate details page from product data
  function populate(product) {
    const thumbsWrap = container.querySelector('.product-thumbs');
    const mainImg = container.querySelector('#mainProductImage');

    // Thumbnails
    if (thumbsWrap) {
      thumbsWrap.innerHTML = '';
      // Normalize image fields: serializers may return either URL string or
      // an object with a `url` property depending on DRF configuration.
      function imgUrl(val) {
        if (!val) return '';
        if (typeof val === 'string') return val;
        if (val && typeof val === 'object' && val.url) return val.url;
        return '';
      }

      const thumbs = [imgUrl(product.image_2), imgUrl(product.image_3), imgUrl(product.image_4)].filter(Boolean);

      thumbs.forEach(src => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'thumb-btn border-0 bg-transparent p-0 mb-2';
        btn.style.cssText = 'cursor:pointer; width:100%; max-width:200px; height:120px;';
        btn.innerHTML = `<img src="${src}" alt="thumb" style="width:100%; height:100%; object-fit:contain; border-radius:8px;">`;
        btn.addEventListener('click', () => { if (mainImg) mainImg.src = src; });
        thumbsWrap.appendChild(btn);
      });

      const mainSrc = imgUrl(product.image) || '';
      if (mainImg && mainSrc) mainImg.src = mainSrc;
    }

    // Standard fields: ensure title & price exist in the right column
    (function ensureTitlePrice() {
      let titleEl = container.querySelector('.product-title');
      let priceEl = container.querySelector('.product-price');
      if (!titleEl || !priceEl) {
        const rightCol = container.querySelector('.col-12.col-lg-4');
        if (rightCol) {
          if (!titleEl) {
            titleEl = document.createElement('h2');
            titleEl.className = 'product-title mb-2';
            rightCol.insertBefore(titleEl, rightCol.firstChild);
          }
          if (!priceEl) {
            priceEl = document.createElement('div');
            priceEl.className = 'product-price mb-3';
            titleEl.parentNode.insertBefore(priceEl, titleEl.nextSibling);
          }
        }
      }
    })();

    setText('.product-title', product.name);
    setText('.product-price', product.price ? `$${product.price}` : '');

    // Field mapping with labels for created detail rows
    const mapping = {
      '.product-category': [product.category, 'Category'],
      '.product-condition': [product.condition, 'Condition'],
      '.product-brand': [product.brand || product.brand_model, 'Brand/Model'],
      '.product-stock': [product.stock !== undefined ? String(product.stock) : '', 'Stock'],
      '.product-delivery': [product.location === 'local' ? 'Tomorrow'
                         : product.location === 'exotic' ? '2 Weeks'
                         : product.location ? 'Standard' : '', 'Delivery'],
      '.product-color': [product.color, 'Color'],
      '.product-storage': [product.storage_ram, 'Storage / RAM'],
      '.product-network': [product.network, 'Network'],
      '.product-battery': [product.battery, 'Battery'],
      '.product-camera': [product.camera, 'Camera'],
      '.product-screen': [product.screen, 'Screen'],
      '.product-processor': [product.processor, 'Processor'],
      '.product-os': [product.os, 'OS'],
      '.product-accessories': [product.accessories, 'Accessories'],
      '.product-warranty': [product.warranty, 'Warranty'],
      '.product-optional': [product.optional_details, 'Additional Details'],
      '.product-available': [product.available !== undefined ? (product.available ? 'Yes' : 'No') : '', 'Available']
    };

    Object.entries(mapping).forEach(([sel, pair]) => {
      const val = pair[0];
      const lbl = pair[1];
      // special-case stock formatting
      if (sel === '.product-stock' && val !== '') {
        const n = Number(val);
        if (!isNaN(n)) {
          setText(sel, n === 0 ? 'Out of stock' : `${n} available`, lbl);
          return;
        }
      }
      setText(sel, val, lbl);
    });

    // Description
    let descEl = container.querySelector('.product-description') || container.querySelector('.description-box p');
    if (descEl) {
      descEl.textContent = product.description || '';
  } else if (isMeaningful(product.description)) {
      try {
        let descWrap = container.querySelector('.description-box');
        if (!descWrap) {
          descWrap = document.createElement('div');
          descWrap.className = 'description-box mb-3';
          // place it near the end of right column (.col-12.col-lg-4)
          const rightCol = container.querySelector('.col-12.col-lg-4') || container.querySelector('.details-container');
          if (rightCol) rightCol.appendChild(descWrap);
          else container.appendChild(descWrap);
        }
  descWrap.innerHTML = `<h5 class="mb-2">Description</h5><p class="product-description">${product.description}</p>`;
      } catch (e) {}
    }

    // Related products
    const relatedGrid = container.querySelector('.related-products-grid');
    if (relatedGrid) {
      relatedGrid.innerHTML = '';
      (product.related || []).forEach(rel => {
        const rimg = (rel.image && typeof rel.image === 'string') ? rel.image : (rel.image && rel.image.url ? rel.image.url : '/static/website/images/default-image.svg');
        const col = document.createElement('div');
        col.className = 'col-6 col-md-3';
        col.innerHTML = `
          <div class="card h-100 border-0 shadow-sm rounded-3 overflow-hidden product-card">
            <a href="/product/${rel.id}/" class="text-decoration-none d-block text-center p-3">
              <img src="${rimg}"
                   class="img-fluid"
                   style="max-height:120px; object-fit:contain; margin:0 auto 8px;">
              <div class="card-body p-0">
                <h6 class="card-title text-dark small mb-1">${rel.name}</h6>
                <p class="card-text fw-bold small" style="color:#9150EC;">$${rel.price}</p>
              </div>
            </a>
          </div>`;
        relatedGrid.appendChild(col);
      });
    }

    // Ensure inline form hidden inputs are created and populated immediately
    try {
      const inlineForm = container.querySelector('form#inlineBuyForm') || container.querySelector('form');
      if (inlineForm) {
        // Temporarily disable submit to avoid race between UI and JS population
        const submitBtn = inlineForm.querySelector('button[type="submit"]');
        if (submitBtn) submitBtn.disabled = true;

        const setHidden = (id, name, value) => {
          let inp = inlineForm.querySelector('#' + id) || inlineForm.querySelector('input[name="' + name + '"]');
          if (!inp) {
            inp = document.createElement('input');
            inp.type = 'hidden';
            inp.id = id;
            inp.name = name;
            inlineForm.appendChild(inp);
          }
          inp.value = (value !== undefined && value !== null) ? String(value) : '';
        };

        setHidden('inline_product_id', 'product_id', product.id || '0');
        setHidden('inline_name', 'name', product.name || 'Unknown Product');
        setHidden('inline_price', 'price', (product.price !== undefined && product.price !== null) ? product.price : '0.00');
        setHidden('inline_condition', 'condition', product.condition || 'N/A');
        setHidden('inline_category', 'category', product.category || 'Uncategorized');
        const imgUrl = (product.image && typeof product.image === 'string') ? product.image : (product.image && product.image.url ? product.image.url : '');
        setHidden('inline_image_url', 'image_url', imgUrl || '/static/website/images/default-image.svg');

        // Re-enable submit after a tiny delay to ensure DOM updated before user can click
        setTimeout(() => { if (submitBtn) submitBtn.disabled = false; }, 30);
      }
    } catch (e) { console.warn('inline form population failed', e); }

    // --- Mobile view sync -------------------------------------------------
    try {
      // main mobile image
      const mobileMain = container.querySelector('#mainProductImageMobile');
      const mobileThumbsWrap = container.querySelector('.product-thumbs-mobile');
      const mobileTitle = container.querySelector('.MobileViewPg h4.fw-semibold');
      const mobilePrice = container.querySelector('.MobileViewPg .product-price');
      const mobileDetailsWrap = container.querySelector('.details-container-mobile');

      // helper to get image url
      function imgUrl(val) {
        if (!val) return '';
        if (typeof val === 'string') return val;
        if (val && typeof val === 'object' && val.url) return val.url;
        return '';
      }

      const mainSrc = imgUrl(product.image) || '';
      if (mobileMain && mainSrc) mobileMain.src = mainSrc;

      if (mobileThumbsWrap) {
        mobileThumbsWrap.innerHTML = '';
        const thumbs = [imgUrl(product.image_2), imgUrl(product.image_3), imgUrl(product.image_4)].filter(Boolean);
        thumbs.forEach(src => {
          const img = document.createElement('img');
          img.src = src;
          img.alt = product.name || 'thumb';
          img.className = 'img-fluid rounded mobile-thumbnail';
          img.style.cssText = 'max-height:80px; object-fit:contain; cursor:pointer;';
          img.addEventListener('click', () => { if (mobileMain) mobileMain.src = src; });
          mobileThumbsWrap.appendChild(img);
        });
      }

      if (mobileTitle) mobileTitle.textContent = product.name || '';
      if (mobilePrice) mobilePrice.textContent = product.price ? `$${product.price}` : '';

      if (mobileDetailsWrap) {
        // Build a compact details list for mobile (only meaningful fields)
        const rows = [];
        const push = (label, value) => {
          if (!value) return;
          rows.push(`<div class="detail-item"><span class="label">${label}</span><span class="value">${value}</span></div>`);
        };

        push('Category', product.category);
        push('Condition', product.condition);
        push('Brand/Model', product.brand || product.brand_model);
        if (product.stock !== undefined) push('Stock', (Number(product.stock) === 0 ? 'Out of stock' : `${product.stock} available`));
        push('Color', product.color);
        push('Storage / RAM', product.storage_ram);
        push('Processor', product.processor);
        push('Battery', product.battery);
        push('Camera', product.camera);
        push('Screen', product.screen);
        push('Network', product.network);
        push('Accessories', product.accessories);
        push('Warranty', product.warranty);
        push('Details', product.optional_details);
        push('Available', product.available !== undefined ? (product.available ? 'Yes' : 'No') : '');

        mobileDetailsWrap.innerHTML = rows.join('');
      }

      // populate mobile inline form hidden inputs if present
      try {
        const setMobileHidden = (id, value) => {
          const el = document.getElementById(id);
          if (el) el.value = (value !== undefined && value !== null) ? String(value) : '';
        };
        setMobileHidden('inline_product_id_mobile', product.id || '');
        setMobileHidden('inline_name_mobile', product.name || '');
        setMobileHidden('inline_price_mobile', (product.price !== undefined && product.price !== null) ? product.price : '');
        setMobileHidden('inline_condition_mobile', product.condition || '');
        setMobileHidden('inline_category_mobile', product.category || '');
        const mobileImgUrl = imgUrl(product.image) || '/static/website/images/default-image.svg';
        setMobileHidden('inline_image_url_mobile', mobileImgUrl);
      } catch (e) { /* ignore mobile form failures */ }
    } catch (e) {
      // non-critical: mobile sync failed
      console.warn('Mobile view sync failed', e);
    }
  }

  // Show container below header
  function showContainer() {
    // Record which main section was visible so we can restore it later
    try {
      previousVisibleSection = null;
      for (const id of MAIN_SECTIONS) {
        const el = document.getElementById(id);
        if (!el) continue;
        const isVisible = el.style.display !== 'none' && el.offsetParent !== null;
        if (isVisible) { previousVisibleSection = id; break; }
      }

      // Hide all main sections to show a focused product detail view
      for (const id of MAIN_SECTIONS) {
        const el = document.getElementById(id);
        if (el && el !== container) el.style.display = 'none';
      }
    } catch (e) { /* ignore section detection errors */ }

    container.style.display = 'block';
    container.classList.add('mt-3', 'product-container');
    container.style.width = '100%';

    if (header && header.parentNode) {
      header.parentNode.insertBefore(container, header.nextSibling);
    }

    const headerHeight = header ? header.offsetHeight : 0;
    const top = container.getBoundingClientRect().top + window.pageYOffset - headerHeight - 8;
    window.scrollTo({ top, behavior: 'smooth' });
  }

  // Hide container
  function hideContainer() {
    container.style.display = 'none';
    // Restore previously visible section if any
    try {
      if (previousVisibleSection) {
        if (typeof window.showSection === 'function') {
          window.showSection(previousVisibleSection);
        } else {
          const el = document.getElementById(previousVisibleSection);
          if (el) {
            el.style.display = 'block';
            try { el.scrollIntoView({ behavior: 'smooth', block: 'start' }); } catch (e) {}
          }
        }
      }
      previousVisibleSection = null;
    } catch (e) {}
  }

  // Load product by ID via API
  function openProductById(pid) {
    if (!pid) return;

    fetch(`/api/product/${pid}/`)
      .then(res => res.ok ? res.json() : Promise.reject('network'))
      .then(json => {
        if (json && json.product) {
          json.product.related = json.related || [];
          populate(json.product);
          showContainer();
        } else {
          throw new Error('invalid payload');
        }
      })
      .catch(err => {
        console.warn('Product JSON load failed, redirecting...', err);
        window.location.href = `/product/${pid}/`;
      });
  }

  // Handle clicks on product images
  document.body.addEventListener('click', function (ev) {
    const target = ev.target.closest('.clickable-image, a.clickable-image, img.clickable-image');
    if (!target) return;

    // Prevent other click handlers (e.g. inline fragment fetch) from
    // also trying to handle this click and overwriting the details DOM.
    if (typeof ev.stopImmediatePropagation === 'function') ev.stopImmediatePropagation();
    ev.preventDefault();

  const pid = target.dataset.productId ||
        target.getAttribute('data-product-id') ||
        target.closest('a')?.dataset.productId;

    if (pid) {
      openProductById(pid);
      return;
    }

    const href = target.closest('a')?.getAttribute('href');
    if (href) {
      const m = href.match(/\/product\/(\d+)\//);
      if (m && m[1]) {
        openProductById(m[1]);
        return;
      }
    }

    // NOTE: inline inputs are populated in populate(product) once the product
    // JSON is received. If a click happens that doesn't trigger the JSON flow
    // (e.g. clicking a raw <a> without data attributes), attempt a best-effort
    // fallback by reading attributes from the clicked element and filling the
    // inline form to avoid empty required fields.
    try {
      // Attempt to derive a minimal product object from the clicked node
      const fallbackProduct = {};
      const alt = target.getAttribute('alt') || target.getAttribute('title') || '';
      if (alt) fallbackProduct.name = alt;
      const src = (target.tagName === 'IMG') ? target.getAttribute('src') : (target.querySelector && target.querySelector('img') ? target.querySelector('img').getAttribute('src') : '');
      if (src) fallbackProduct.image = src;
      // If pid exists in data attributes earlier we already returned. As a defensive measure
      // try to set the inline form with any info we have available.
      const inlineForm = container.querySelector('form#inlineBuyForm') || container.querySelector('form');
      if (inlineForm) {
        const setIfEmpty = (selectorName, val) => {
          const el = inlineForm.querySelector(selectorName) || inlineForm.querySelector('input[name="' + selectorName + '"]');
          if (el && (!el.value || String(el.value).trim() === '')) el.value = val || '';
        };
        if (fallbackProduct.name) setIfEmpty('name', fallbackProduct.name);
        if (src) setIfEmpty('image_url', src);
        // product_id and price are critical; leave them empty rather than guessing
      }
    } catch (e) { /* ignore fallback failures */ }

    // Signal to other scripts that the inline product details (and its form)
    // have been populated. Other modules can listen for this event to rebind
    // handlers or refresh UI.
    try {
      const ev = new CustomEvent('productDetailsLoaded', { detail: { product: product } });
      container.dispatchEvent(ev);
    } catch (e) {
      // ignore if CustomEvent is not available
    }

    // Fallback: just show the clicked image
    const img = target.tagName === 'IMG' ? target : target.querySelector('img');
    if (img) {
      const mainImg = container.querySelector('#mainProductImage');
      if (mainImg) mainImg.src = img.src;
      setText('.product-title', img.alt || '');
      showContainer();
    }
  });

  // Hide details when clicking outside
  document.addEventListener('click', function (e) {
    if (!container) return;
    // If clicking inside the container or on a clickable-image, do nothing
    if (e.target.closest('#product_details_page') || e.target.closest('.clickable-image')) return;
    // If the container is showing a simple loading state, do not immediately hide it
    const loading = container.textContent && container.textContent.trim().toLowerCase().startsWith('loading');
    if (loading) return;
    if (container.style.display !== 'none') hideContainer();
  });

  // Ensure close button exists
  (function ensureCloseBtn() {
    if (!container) return;
    if (container.querySelector('.product-close-btn')) return;

    const wrap = document.createElement('div');
  wrap.style.position = 'absolute';
  wrap.style.right = '18px';
  wrap.style.top = '18px';
  wrap.style.zIndex = '9999';
  wrap.style.pointerEvents = 'auto';
    wrap.innerHTML = `<button type="button" class="product-close-btn btn btn-sm btn-light border">×</button>`;
    wrap.querySelector('.product-close-btn').addEventListener('click', hideContainer);

    container.style.position = 'relative';
    container.appendChild(wrap);
  })();
});
