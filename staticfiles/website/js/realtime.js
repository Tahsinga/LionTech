(function () {
  // Simple WebSocket client to listen for site updates and dispatch DOM updates
  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
  const host = window.location.host;
  const socketUrl = `${protocol}://${host}/ws/updates/`;

  let socket;
  function connect() {
    socket = new WebSocket(socketUrl);
    socket.addEventListener('open', () => console.info('realtime: connected'));
    socket.addEventListener('message', (ev) => {
      try {
        const payload = JSON.parse(ev.data);
        handleUpdate(payload);
      } catch (e) { console.warn('realtime: invalid message', e); }
    });
    socket.addEventListener('close', () => {
      console.warn('realtime: disconnected, retrying in 2s');
      setTimeout(connect, 2000);
    });
  }

  function handleUpdate(msg) {
    if (!msg || !msg.data) return;
    const p = msg.data;
    const model = msg.model || p.model || null;
    // Example: update cart count badge when cartOrder changed
    if (p.model === 'cartOrder') {
      try {
        // fetch cart summary to keep server and client in sync
        if (typeof fetchCartData === 'function') fetchCartData();
      } catch (e) {}
    }

    // Example: product change -> optionally refresh product grid via AJAX
    if (p.model === 'Product') {
      try {
        // If product list exists, re-fetch products endpoint
        if (document.getElementById('productList')) {
          // naive: reload products fragment
          fetch(window.location.pathname)
            .then(r => r.text())
            .then(html => {
              const doc = new DOMParser().parseFromString(html, 'text/html');
              const newList = doc.getElementById('productList');
              const oldList = document.getElementById('productList');
              if (newList && oldList) oldList.replaceWith(newList);
              // Re-run any initializers
              if (typeof initializeProductCarousels === 'function') initializeProductCarousels();
            })
            .catch(() => {});
        }
      } catch (e) {}
    }

    // Order updates: update order row/status in the Orders UI if present
    try {
      if (model === 'Order' || (p.order_id && p.delivery_status)) {
        const orderId = p.order_id;
        const status = p.delivery_status;
        if (orderId) {
          // Look for an element representing the order. Convention: data-order-id attribute
          const orderEl = document.querySelector(`[data-order-id="${orderId}"]`);
          if (orderEl) {
            // Try to find a child with class 'order-status' and update text
            const statusEl = orderEl.querySelector('.order-status');
            if (statusEl) {
              statusEl.textContent = status;
            } else {
              // If no specific status element, append/update a small badge
              let badge = orderEl.querySelector('.order-status-badge');
              if (!badge) {
                badge = document.createElement('span');
                badge.className = 'order-status-badge';
                orderEl.appendChild(badge);
              }
              badge.textContent = status;
            }
            return;
          }

          // If we didn't find the order element, refresh the orders container if it exists
          const ordersContainer = document.getElementById('ordersContainer');
          if (ordersContainer) {
            // naive: re-request current page and replace orders fragment
            fetch(window.location.pathname)
              .then(r => r.text())
              .then(html => {
                const doc = new DOMParser().parseFromString(html, 'text/html');
                const newOrders = doc.getElementById('ordersContainer');
                if (newOrders) ordersContainer.replaceWith(newOrders);
              }).catch(() => {});
          }
        }
      }
    } catch (e) { console.warn('realtime: order update failed', e); }
  }

  // Start
  if (window.location.host) connect();
})();
