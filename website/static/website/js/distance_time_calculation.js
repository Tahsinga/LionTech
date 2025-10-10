// Harare CBD coordinates
    const CBD = { lat: -17.8292, lng: 31.0522 };

    // Haversine distance (km)
    function haversine(lat1, lon1, lat2, lon2) {
      const R = 6371;
      const toRad = d => d * Math.PI / 180;
      const dLat = toRad(lat2 - lat1);
      const dLon = toRad(lon2 - lon1);
      const a = Math.sin(dLat/2)**2 + Math.cos(toRad(lat1)) *Math.cos(toRad(lat2)) * Math.sin(dLon/2)**2;
      const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
      return R * c;
    }

    // Determine delivery estimate per Harare cutoff policy :contentReference[oaicite:5]{index=5}
    function estimateDeliveryDate(now) {
      const cutoffHour = 10;
      const weekday = now.getDay(); // 0=Sun…6=Sat
      let deliverDay = new Date(now);
      if (weekday === 0 || weekday === 6) {
        // weekend → Monday
        const daysToAdd = (8 - weekday);
        deliverDay.setDate(now.getDate() + daysToAdd);
        deliverDay.setHours(8,0,0);
      } else if (now.getHours() < cutoffHour) {
        deliverDay.setDate(now.getDate());
        deliverDay.setHours(15,0,0);
      } else {
        const next = new Date(now);
        next.setDate(now.getDate() + 1);
        const nd = next.getDay();
        if (nd === 6) next.setDate(next.getDate() + 2);
        if (nd === 0) next.setDate(next.getDate() + 1);
        deliverDay = new Date(next.setHours(15,0,0));
      }
      return deliverDay;
    }

    // Format countdown
    function formatRemaining(ms) {
      const sec = Math.floor(ms / 1000) % 60;
      const min = Math.floor(ms / 1000 / 60) % 60;
      const hr  = Math.floor(ms / 1000 / 3600);
      return `${hr}h ${min}m ${sec}s`;
    }

    // Track multiple checkouts
    const checkoutLog = [];

    function onCheckout(customerLat, customerLng) {
      const now = new Date();
      const dist = haversine(CBD.lat, CBD.lng, customerLat, customerLng);
      const deliverAt = estimateDeliveryDate(now);
      const id = Date.now();
      checkoutLog.push({ id, now, dist, deliverAt });
      renderCheckoutEntry({ id, now, dist, deliverAt });
    }

    // Render one row
    function renderCheckoutEntry({ id, now, dist, deliverAt }) {
      const container = document.getElementById('checkout-log');
      const row = document.createElement('div');
      row.id = `entry-${id}`;
      row.innerHTML = `
        <strong>Checkout at:</strong> ${now.toLocaleString()} |
        <strong>Distance:</strong> ${dist.toFixed(2)} km |
        <strong>ETA:</strong> ${deliverAt.toLocaleString()} |
        <span class="countdown">calculating...</span>
      `;
      container.prepend(row);

      // countdown update
      const span = row.querySelector('.countdown');
      function tick() {
        const rem = deliverAt - new Date();
        if (rem <= 0) {
          span.textContent = 'Arrived';
          clearInterval(timer);
        } else {
          span.textContent = formatRemaining(rem);
        }
      }
      tick();
      const timer = setInterval(tick, 1000);
    }

    // Hook into your checkout button
    document.getElementById('checkoutBtn').addEventListener('click', () => {
      const lat = parseFloat(document.getElementById('lat').value);
      const lng = parseFloat(document.getElementById('lng').value);
      if (isNaN(lat) || isNaN(lng)) {
        alert('Please select a valid location on map.');
        return;
      }
      onCheckout(lat, lng);
      // then send request to backend as normal...
    });