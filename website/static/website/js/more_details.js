function toggleMoreDetails(button) {
    const details = button.parentElement.nextElementSibling;

      if (details.classList.contains('d-none')) {
        details.classList.remove('d-none');
        button.textContent = 'Less Details';
      } else {
        details.classList.add('d-none');
        button.textContent = 'More Details';
      }
    }
