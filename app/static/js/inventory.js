document.addEventListener('DOMContentLoaded', () => {
  const tbody = document.querySelector('.orders-table tbody');
  const createForm = document.getElementById('inventoryCreateForm');

  function showMessage(message) {
    window.alert(message);
  }

  async function loadProducts() {
    const res = await fetch('/api/inventory');
    const data = await res.json();
    if (!data.ok) {
      showMessage(data.error || 'Failed to load inventory.');
      return;
    }

    tbody.innerHTML = '';
    data.products.forEach((product) => {
      const row = document.createElement('tr');
      row.innerHTML = `
        <td>
          <strong>${product.name}</strong>
          <div class="text-muted" style="font-size:0.85rem;">${product.slug}</div>
        </td>
        <td><input type="text" value="${product.category || ''}" class="category-input" data-slug="${product.slug}" style="width:130px"></td>
        <td><input type="number" value="${product.stock || 0}" class="stock-input" data-slug="${product.slug}" style="width:80px"></td>
        <td><input type="number" value="${product.price || 0}" class="price-input" data-slug="${product.slug}" style="width:100px"></td>
        <td><span class="status-badge">${product.stock > 0 ? 'In Stock' : 'Out'}</span></td>
        <td>
          <button class="btn btn-primary save-btn" data-slug="${product.slug}">Save</button>
          <button class="btn btn-danger del-btn" data-slug="${product.slug}">Delete</button>
        </td>
      `;
      tbody.appendChild(row);
    });

    document.querySelectorAll('.save-btn').forEach((button) => {
      button.addEventListener('click', async () => {
        const slug = button.dataset.slug;
        const category = document.querySelector(`.category-input[data-slug="${slug}"]`).value.trim();
        const stock = Number(document.querySelector(`.stock-input[data-slug="${slug}"]`).value);
        const price = Number(document.querySelector(`.price-input[data-slug="${slug}"]`).value);
        const res = await fetch(`/api/inventory/${slug}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ category, stock, price }),
        });
        const data = await res.json();
        if (!data.ok) {
          showMessage(data.error || 'Save failed.');
          return;
        }
        await loadProducts();
      });
    });

    document.querySelectorAll('.del-btn').forEach((button) => {
      button.addEventListener('click', async () => {
        if (!window.confirm('Delete this product?')) return;
        const res = await fetch(`/api/inventory/${button.dataset.slug}`, { method: 'DELETE' });
        const data = await res.json();
        if (!data.ok) {
          showMessage(data.error || 'Delete failed.');
          return;
        }
        await loadProducts();
      });
    });
  }

  createForm?.addEventListener('submit', async (event) => {
    event.preventDefault();
    const formData = new FormData(createForm);
    const payload = Object.fromEntries(formData.entries());
    payload.price = Number(payload.price || 0);
    payload.stock = Number(payload.stock || 0);

    const res = await fetch('/api/inventory', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!data.ok) {
      showMessage(data.error || 'Create failed.');
      return;
    }

    createForm.reset();
    createForm.elements.badge.value = 'New';
    createForm.elements.stock.value = '0';
    await loadProducts();
    showMessage('Product saved to Cosmos DB.');
  });

  loadProducts();
});
