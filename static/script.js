if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/service-worker.js')
      .then(registration => {
        console.log('ServiceWorker registered with scope:', registration.scope);
      })
      .catch(error => {
        console.log('ServiceWorker registration failed:', error);
      });
  });
}

async function loadProducts() {
  
    const response = await fetch('/products');
  const products = await response.json();

  const container = document.getElementById('products');
  container.innerHTML = '';

  products.forEach(p => {
    const div = document.createElement('div');
    div.className = "p-4 bg-white shadow rounded";

    div.innerHTML = `
      <h2 class="text-lg font-semibold">${p.name}</h2>
      <p>Price: ${p.price.toFixed(2)} ${p.currency || 'LBP'}</p>
      <p>Stock: ${p.stock} ${p.unit_type || 'piece'}</p>
      <input type="number" min="1" value="1" class="quantity border mt-2 px-2 py-1 w-16"/>
      <button class="buy bg-green-500 text-white px-3 py-1 mt-2 rounded" data-barcode="${p.barcode}">Sell</button>
    `;

    div.querySelector('.buy').onclick = async function () {
      const quantity = parseFloat(div.querySelector('.quantity').value);
      const barcode = this.dataset.barcode;

      const res = await fetch('/sell', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ barcode, quantity })
      });

      const data = await res.json();

      if (res.ok) {
        showReceipt(data);
        loadProducts();
      } else {
        alert(data.error || 'Error');
      }
    };

    container.appendChild(div);
  });
}

function showReceipt(data) {
  const receipt = document.getElementById('receipt');
  const content = document.getElementById('receipt-content');

  const now = new Date().toLocaleString();
  content.innerHTML = `
    <p><strong>Date:</strong> ${now}</p>
    <p><strong>Product:</strong> ${data.product}</p>
    <p><strong>Quantity:</strong> ${data.quantity}</p>
    <p><strong>Unit Price:</strong> ${data.price.toFixed(2)} LBP</p>
    <p><strong>Total:</strong> ${data.total.toFixed(2)} LBP</p>
  `;
  receipt.classList.remove('hidden');
}

function closeReceipt() {
  document.getElementById('receipt').classList.add('hidden');
}

// Initial load
loadProducts();
