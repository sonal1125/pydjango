document.addEventListener('DOMContentLoaded', function () {
    const pendingProductId = localStorage.getItem('pending_add_to_cart');
    if (pendingProductId) {
        localStorage.removeItem('pending_add_to_cart');  // ✅ move this up before fetch

        fetch('/cart/add/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: JSON.stringify({ product_id: pendingProductId }),
        })
        .then(res => {
            if (!res.ok) throw new Error('Failed to auto-add to cart');
            return res.json();
        })
        .then(data => {
            console.log('Auto-added product after login:', data);
            updateCartCount();
        })
        .catch(err => console.error('Error auto-adding to cart after login:', err));
    }
    
    
    // Force-hide popup on page load
    const cartPopup = document.getElementById('cart-popup');
    const closeBtn = document.getElementById('close-popup-btn');

    // Hide popup on load
    if (cartPopup) cartPopup.style.display = 'none';

    // Add click handler to close button
    if (closeBtn && cartPopup) {
        closeBtn.addEventListener('click', () => {
            cartPopup.style.display = 'none';
        });
    }

    // CSRF helper
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

    const csrftoken = getCookie('csrftoken');

    // Handle Add to Cart button click
    function bindAddToCartButtons() {
        document.querySelectorAll('.add-to-cart-btn').forEach(button => {
            button.addEventListener('click', function (e) {
                e.preventDefault();

                const productId = this.dataset.productId;
                const productDiv = this.closest('.div-prod');
                const productName = productDiv.querySelector('.h5-prod-name').textContent;
                const productImg = productDiv.querySelector('img').src;
                const msgSpan = productDiv.querySelector('.in-cart-msg');

                fetch('/cart/add/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrftoken,
                    },
                    body: JSON.stringify({ product_id: productId }),
                })
                .then(response => {
                    if (response.status === 401) {
                        alert("Please log in to add items to your cart.");
                        localStorage.setItem('pending_add_to_cart', productId);
                        window.location.href = '/login/?next=' + window.location.pathname;
                        return null; // explicitly return null so next then won't run
                    }
                    return response.json();
                })
                .then(data => {
                    if (!data) return; // Prevent further execution if redirected
                
                    // Everything below runs only when user is logged in and response is valid

                    // Hide button
                    this.style.display = 'none';

                    // Show "In cart" message
                    if (msgSpan) {
                        msgSpan.textContent = data.message || 'In cart';
                        msgSpan.style.display = 'inline';
                        msgSpan.style.color = 'green';
                    }

                    // Show popup
                    if (cartPopup) {
                        document.getElementById('popup-product-name').textContent = productName;
                        document.getElementById('popup-product-img').src = productImg;
                        cartPopup.style.display = 'block';
                    }

                    updateCartCount(); // Update navbar cart count
                })
                .catch(error => {
                    console.error('Error:', error);
                    if (msgSpan) {
                        msgSpan.textContent = 'Failed to add to cart';
                        msgSpan.style.color = 'red';
                        msgSpan.style.display = 'inline';
                        setTimeout(() => {
                            msgSpan.textContent = '';
                        }, 3000);
                    }
                });
            });
        });
    }

    // Handle popup close button
    // const closeBtn = document.getElementById('close-popup-btn');
    // if (closeBtn && cartPopup) {
    //     closeBtn.addEventListener('click', () => {
    //         cartPopup.style.display = 'none';
    //     });
    // }

    // Update cart count
    function updateCartCount() {
        fetch('/cart/count/')
            .then(response => response.json())
            .then(data => {
                const countElement = document.getElementById('cart-count');
                if (countElement) {
                    countElement.textContent = data.count;
                }
            });
    }

    // Initial binding
    bindAddToCartButtons();

    // Handle pagination via AJAX
    document.body.addEventListener('click', function (e) {
        if (e.target.tagName === 'A' && e.target.closest('.pagination')) {
            e.preventDefault();
            const url = e.target.href;

            fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
                .then(response => response.text())
                .then(html => {
                    document.querySelector('#product-grid-container').innerHTML = html;
                    // window.scrollTo({ top: 0, behavior: 'smooth' }); // Optional: scroll to top
                    bindAddToCartButtons();  // Re-bind after pagination
                });
        }
    });

  const mainImg = document.getElementById("mainImage");
  const zoomLens = document.getElementById("zoomLens");
  const zoomResult = document.getElementById("zoomResult");

  if (!mainImg) return;

  function updateZoomBackground() {
    zoomResult.style.backgroundImage = `url('${mainImg.src}')`;
  }

  updateZoomBackground();  // initialize

  mainImg.addEventListener("mouseenter", () => {
    zoomLens.style.display = "block";
    zoomResult.style.display = "block";
  });

  mainImg.addEventListener("mouseleave", () => {
    zoomLens.style.display = "none";
    zoomResult.style.display = "none";
  });

  mainImg.addEventListener("mousemove", function (e) {
    const bounds = mainImg.getBoundingClientRect();
    const x = e.pageX - window.scrollX - bounds.left - zoomLens.offsetWidth / 2;
    const y = e.pageY - window.scrollY - bounds.top - zoomLens.offsetHeight / 2;

    const maxX = mainImg.offsetWidth - zoomLens.offsetWidth;
    const maxY = mainImg.offsetHeight - zoomLens.offsetHeight;

    const lensX = Math.max(0, Math.min(x, maxX));
    const lensY = Math.max(0, Math.min(y, maxY));

    zoomLens.style.left = bounds.left + lensX + "px";
    zoomLens.style.top = bounds.top + lensY + "px";

    const ratioX = zoomResult.offsetWidth / zoomLens.offsetWidth;
    const ratioY = zoomResult.offsetHeight / zoomLens.offsetHeight;

    zoomResult.style.backgroundPosition = `-${lensX * ratioX}px -${lensY * ratioY}px`;
  });
});

// Switch main image when thumbnail is clicked
function changeMainImage(thumb) {
  const mainImg = document.getElementById("mainImage");
  mainImg.src = thumb.src;

  // update zoom background
  const zoomResult = document.getElementById("zoomResult");
  if (zoomResult) {
    zoomResult.style.backgroundImage = `url('${thumb.src}')`;
  }
}


