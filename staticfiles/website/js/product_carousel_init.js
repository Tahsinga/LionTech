document.addEventListener('DOMContentLoaded', function() {
  // Assign different animation directions per product carousel using product id
  document.querySelectorAll('[id^="productCarousel"]').forEach(carousel => {
    const id = carousel.id.replace('productCarousel', '');
    const pid = parseInt(id, 10) || 0;
    // pick direction based on product id
    const dirs = ['slide-left', 'slide-right', 'slide-up', 'slide-down'];
    const cls = dirs[pid % dirs.length];
    carousel.classList.add(cls);

    // initialize bootstrap carousel with interval and pause on hover
    try {
      const bsCarousel = new bootstrap.Carousel(carousel, {
        interval: 3000 + (pid % 3) * 500, // slight variety in speed
        ride: 'carousel',
        pause: 'hover',
      });
    } catch (e) {
      // bootstrap not loaded yet or not present — ignore
      console.warn('Bootstrap carousel init failed for', carousel.id, e);
    }
  });
});
