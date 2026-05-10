const CART_KEY = 'smartretail_cart';
const LAST_ORDER_MESSAGE_KEY = 'smartretail_last_order_message';
const API_BASE = '/api';

const appState = {
  cart: [],
  orders: [],
};

function readStorage(key, fallback) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch (_) {
    return fallback;
  }
}

function writeStorage(key, value) {
  localStorage.setItem(key, JSON.stringify(value));
}

function money(value) {
  return `$${Number(value || 0).toFixed(2)}`;
}

function formatDate(value) {
  return new Date(value || Date.now()).toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
}

function isLoggedIn() {
  return Boolean(window.__USER_ID__);
}

function getCartLocal() {
  return readStorage(CART_KEY, []);
}

function saveCartLocal(cart) {
  writeStorage(CART_KEY, cart);
}

function getProductData(el) {
  return {
    slug: el.dataset.slug,
    name: el.dataset.name,
    category: el.dataset.category,
    price: Number(el.dataset.price || 0),
    stock: Number(el.dataset.stock || 0),
    image: el.dataset.image,
    desc: el.dataset.desc,
  };
}

function createToast(title, message) {
  let toast = document.querySelector('.toast-notification');
  if (!toast) {
    toast = document.createElement('div');
    toast.className = 'toast-notification hide';
    document.body.appendChild(toast);
  }
  toast.innerHTML = `<strong>${title}</strong><div>${message}</div>`;
  toast.classList.remove('hide');
  clearTimeout(window.__smartRetailToastTimer);
  window.__smartRetailToastTimer = setTimeout(() => toast.classList.add('hide'), 2600);
}

async function fetchCart() {
  if (!isLoggedIn()) {
    return getCartLocal();
  }
  try {
    const response = await fetch(`${API_BASE}/cart`);
    const payload = await response.json();
    if (payload.ok) {
      return payload.cart.items || [];
    }
  } catch (_) {}
  return getCartLocal();
}

async function fetchOrders() {
  if (!isLoggedIn()) return [];
  try {
    const response = await fetch(`${API_BASE}/orders`);
    const payload = await response.json();
    if (payload.ok) {
      return payload.orders || [];
    }
  } catch (_) {}
  return [];
}

function cartTotals(cart) {
  const itemCount = cart.reduce((sum, item) => sum + Number(item.qty || 0), 0);
  const subtotal = cart.reduce((sum, item) => sum + Number(item.qty || 0) * Number(item.price || 0), 0);
  const delivery = itemCount > 0 ? 49 : 0;
  const tax = subtotal * 0.18;
  const total = subtotal + delivery + tax;
  return { itemCount, subtotal, delivery, tax, total };
}

function syncCartIndicators() {
  const totals = cartTotals(appState.cart);
  document.querySelectorAll('#navCartCount').forEach((el) => {
    el.textContent = String(totals.itemCount);
  });
  const sidebarCount = document.getElementById('sidebarCartCount');
  if (sidebarCount) sidebarCount.textContent = String(totals.itemCount);

  const countEl = document.getElementById('cartCount');
  const subtotalEl = document.getElementById('cartSubtotal');
  const taxEl = document.getElementById('summaryTax');
  const totalEl = document.getElementById('cartTotal');
  const deliveryEl = document.getElementById('cartDelivery');

  if (countEl) countEl.textContent = String(totals.itemCount);
  if (subtotalEl) subtotalEl.textContent = money(totals.subtotal);
  if (taxEl) taxEl.textContent = money(totals.tax);
  if (totalEl) totalEl.textContent = money(totals.total);
  if (deliveryEl) deliveryEl.textContent = money(totals.delivery);

  const modalTotal = document.getElementById('cartModalTotal');
  if (modalTotal) modalTotal.textContent = money(totals.total);
}

async function refreshCart() {
  appState.cart = await fetchCart();
  syncCartIndicators();
  renderCartDrawer();
  renderCartPage();
}

async function refreshOrders() {
  appState.orders = await fetchOrders();
  renderRecentOrdersTable();
  renderOrdersPage();
}

async function addToCart(product, qty = 1) {
  if (isLoggedIn()) {
    try {
      const response = await fetch(`${API_BASE}/add-to-cart`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ slug: product.slug, qty }),
      });
      const payload = await response.json();
      if (!payload.ok) {
        createToast('Add failed', payload.error || 'Unable to add this item right now.');
        return;
      }
    } catch (_) {
      createToast('Network error', 'Unable to add this item right now.');
      return;
    }
  } else {
    const cart = getCartLocal();
    const existing = cart.find((item) => item.slug === product.slug);
    if (existing) {
      existing.qty += qty;
    } else {
      cart.push({ ...product, qty });
    }
    saveCartLocal(cart);
  }
  await refreshCart();
  createToast('Added to cart successfully', `${product.name} was added to your cart.`);
}

async function updateCartItem(slug, change) {
  if (isLoggedIn()) {
    const endpoint = change > 0 ? `${API_BASE}/add-to-cart` : `${API_BASE}/remove-from-cart`;
    const method = change > 0 ? 'POST' : 'DELETE';
    const body = JSON.stringify({ slug, qty: Math.abs(change) });
    await fetch(endpoint, { method, headers: { 'Content-Type': 'application/json' }, body });
  } else {
    let cart = getCartLocal();
    const item = cart.find((entry) => entry.slug === slug);
    if (!item) return;
    item.qty += change;
    cart = cart.filter((entry) => entry.qty > 0);
    saveCartLocal(cart);
  }
  await refreshCart();
}

async function removeCartItem(slug) {
  if (isLoggedIn()) {
    await fetch(`${API_BASE}/remove-from-cart`, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ slug }),
    });
  } else {
    saveCartLocal(getCartLocal().filter((item) => item.slug !== slug));
  }
  await refreshCart();
  createToast('Removed from cart', 'Item removed from your cart.');
}

function openCartDrawer() {
  const drawer = document.getElementById('cartModal');
  if (!drawer) return;
  renderCartDrawer();
  drawer.hidden = false;
}

function closeCartDrawer() {
  const drawer = document.getElementById('cartModal');
  if (drawer) drawer.hidden = true;
}

function statusClass(status) {
  const normalized = String(status || 'Ordered').toLowerCase();
  if (normalized === 'delivered') return 'status-delivered';
  if (normalized === 'shipped') return 'status-shipped';
  return 'status-ordered';
}

function renderCartDrawer() {
  const list = document.getElementById('cartItemsList');
  if (!list) return;

  if (!appState.cart.length) {
    list.innerHTML = `
      <div class="empty-state retail-panel">
        <h3>Your cart is empty</h3>
        <p>Add products to see them here instantly.</p>
      </div>
    `;
    return;
  }

  list.innerHTML = appState.cart.map((item) => `
    <article class="drawer-cart-item" data-slug="${item.slug}">
      <img src="${item.image || ''}" alt="${item.name}">
      <div class="drawer-cart-meta">
        <div class="drawer-cart-row">
          <strong>${item.name}</strong>
          <strong>${money((item.qty || 0) * (item.price || 0))}</strong>
        </div>
        <p>${money(item.price)} each</p>
        <div class="drawer-cart-actions">
          <div class="drawer-qty-control">
            <button type="button" data-action="dec">-</button>
            <span>${item.qty}</span>
            <button type="button" data-action="inc">+</button>
          </div>
          <button type="button" class="drawer-remove-btn" data-action="remove">Remove</button>
        </div>
      </div>
    </article>
  `).join('');
}

function renderCartPage() {
  const list = document.getElementById('cartList');
  if (!list) return;

  if (!appState.cart.length) {
    list.innerHTML = `
      <div class="empty-state">
        <h3>Your cart is empty</h3>
        <p>Add products to build your order.</p>
        <a href="/products" class="retail-primary-btn" style="display:inline-flex; width:auto; margin-top:1rem;">Browse Products</a>
      </div>
    `;
    return;
  }

  list.innerHTML = appState.cart.map((item) => `
    <article class="ecom-cart-row" data-slug="${item.slug}">
      <div class="ecom-cart-img-wrap">
        <img src="${item.image || ''}" alt="${item.name}" class="ecom-cart-img">
      </div>
      <div class="ecom-cart-info">
        <strong>${item.name}</strong>
        <p>${item.category || 'Smart Retail Product'}</p>
        <span class="ecom-cart-price">${money(item.price)}</span>
      </div>
      <div class="ecom-cart-qty">
        <button type="button" data-action="dec">-</button>
        <span>${item.qty}</span>
        <button type="button" data-action="inc">+</button>
      </div>
      <div class="ecom-cart-total">${money((item.qty || 0) * (item.price || 0))}</div>
      <button type="button" class="btn-icon" data-action="remove">X</button>
    </article>
  `).join('');
}

function renderRecentOrdersTable() {
  const tableBody = document.getElementById('recentOrdersBody');
  if (!tableBody) return;

  if (!appState.orders.length) {
    tableBody.innerHTML = `<tr><td colspan="6" class="table-empty">No orders yet. Place one from your cart to see it here.</td></tr>`;
    return;
  }

  tableBody.innerHTML = appState.orders.slice(0, 4).map((order) => `
    <tr>
      <td>#${order.order_code || order.id}</td>
      <td>${formatDate(order.created_at)}</td>
      <td>${order.count} ${order.count > 1 ? 'items' : 'item'}</td>
      <td>${money(order.total)}</td>
      <td><span class="status-pill ${statusClass(order.status)}">${order.status}</span></td>
      <td><button type="button" class="retail-outline-btn compact recent-order-btn" data-order-id="${order.id}">View Details</button></td>
    </tr>
  `).join('');
}

function renderOrdersPage() {
  const list = document.getElementById('ordersList');
  if (!list) return;

  const message = readStorage(LAST_ORDER_MESSAGE_KEY, null);
  const messageBox = document.getElementById('orderMessage');
  if (messageBox && message) {
    messageBox.hidden = false;
    messageBox.innerHTML = `<strong>${message.title}</strong><div>${message.message}</div>`;
    localStorage.removeItem(LAST_ORDER_MESSAGE_KEY);
  }

  const filterValue = document.getElementById('orderStatusFilter')?.value || 'All';
  const filteredOrders = filterValue === 'All'
    ? appState.orders
    : appState.orders.filter((order) => order.status === filterValue);

  const totalOrders = document.getElementById('totalOrders');
  const totalOrdered = document.getElementById('totalOrdered');
  const totalShipped = document.getElementById('totalShipped');
  const totalDelivered = document.getElementById('totalDelivered');
  if (totalOrders) totalOrders.textContent = String(appState.orders.length);
  if (totalOrdered) totalOrdered.textContent = String(appState.orders.filter((order) => order.status === 'Ordered').length);
  if (totalShipped) totalShipped.textContent = String(appState.orders.filter((order) => order.status === 'Shipped').length);
  if (totalDelivered) totalDelivered.textContent = String(appState.orders.filter((order) => order.status === 'Delivered').length);

  if (!filteredOrders.length) {
    list.innerHTML = `
      <div class="retail-panel empty-state">
        <h3>No orders found</h3>
        <p>Place an order from the cart and it will appear here with live status updates.</p>
      </div>
    `;
    return;
  }

  list.innerHTML = filteredOrders.map((order) => {
    const thumbnails = (order.items || []).slice(0, 3).map((item) => `
      <img class="order-product-thumb" src="${item.image || ''}" alt="${item.name}">
    `).join('');
    const extraItems = (order.items || []).length - 3;
    return `
      <article class="detailed-order-card retail-panel">
        <div class="detailed-order-top">
          <div>
            <span class="order-meta-label">Order ID</span>
            <strong class="order-meta-strong">#${order.order_code || order.id}</strong>
          </div>
          <div>
            <span class="order-meta-label">Date</span>
            <strong class="order-meta-strong">${formatDate(order.created_at)}</strong>
          </div>
          <div>
            <span class="order-meta-label">Total Amount</span>
            <strong class="order-total-strong">${money(order.total)}</strong>
          </div>
          <div>
            <span class="status-pill ${statusClass(order.status)}">${order.status}</span>
          </div>
        </div>
        <div class="detailed-order-bottom">
          <div class="order-product-strip">
            ${thumbnails}
            ${extraItems > 0 ? `<span class="order-product-thumb-more">+${extraItems}</span>` : ''}
          </div>
          <div>
            <span class="order-meta-label">Items</span>
            <strong class="order-meta-strong">${order.count} ${order.count > 1 ? 'Items' : 'Item'}</strong>
          </div>
          <div>
            <span class="order-meta-label">Payment Method</span>
            <strong class="order-meta-strong">${order.payment_method || 'UPI'}</strong>
          </div>
          <div>
            <span class="order-meta-label">${order.delivery_label || 'Delivery Status'}</span>
            <strong class="order-meta-strong">${formatDate(order.delivery_date || order.created_at)}</strong>
          </div>
          <button type="button" class="retail-outline-btn order-detail-btn" data-order-id="${order.id}">View Details</button>
        </div>
      </article>
    `;
  }).join('');
}

function openOrderDetail(orderId) {
  const order = appState.orders.find((entry) => entry.id === orderId);
  const modal = document.getElementById('orderDetailModal');
  const content = document.getElementById('orderDetailContent');
  if (!order || !modal || !content) return;

  content.innerHTML = `
    <h2 style="margin:0 0 0.35rem;">Order #${order.order_code || order.id}</h2>
    <p class="text-muted" style="margin-bottom:1rem;">Placed on ${formatDate(order.created_at)} • ${order.status}</p>
    <div class="summary-stack" style="padding-top:0;">
      <div class="summary-line"><span>Payment Method</span><strong>${order.payment_method || 'UPI'}</strong></div>
      <div class="summary-line"><span>${order.delivery_label || 'Delivery Date'}</span><strong>${formatDate(order.delivery_date || order.created_at)}</strong></div>
      <div class="summary-line"><span>Total Items</span><strong>${order.count}</strong></div>
      <div class="summary-line"><span>Grand Total</span><strong>${money(order.total)}</strong></div>
    </div>
    <div class="order-modal-items">
      ${(order.items || []).map((item) => `
        <article class="order-modal-item">
          <img src="${item.image || ''}" alt="${item.name}">
          <div>
            <strong>${item.name}</strong>
            <div class="text-muted">${item.category || 'Smart Retail Product'}</div>
            <div class="text-muted">Qty: ${item.qty}</div>
          </div>
          <strong>${money((item.line_total || (item.qty || 0) * (item.price || 0)))}</strong>
        </article>
      `).join('')}
    </div>
  `;
  modal.hidden = false;
}

function closeOrderDetail() {
  const modal = document.getElementById('orderDetailModal');
  if (modal) modal.hidden = true;
}

async function placeOrder() {
  const cart = appState.cart.length ? appState.cart : await fetchCart();
  if (!cart.length) {
    createToast('Cart is empty', 'Add products before placing an order.');
    return;
  }

  try {
    let payload;
    if (isLoggedIn()) {
      const response = await fetch(`${API_BASE}/place-order`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ items: cart }),
      });
      payload = await response.json();
    } else {
      const response = await fetch(`${API_BASE}/orders`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ items: cart }),
      });
      payload = await response.json();
      if (payload.ok) saveCartLocal([]);
    }

    if (!payload.ok) {
      createToast('Order failed', payload.error || 'Could not place your order.');
      return;
    }

    writeStorage(LAST_ORDER_MESSAGE_KEY, {
      title: 'Order placed successfully',
      message: payload.message || 'Your order is now available on the orders page.',
    });
    closeCartDrawer();
    await refreshCart();
    await refreshOrders();
    createToast('Order placed successfully', 'Your cart was cleared and the order is now in My Orders.');
  } catch (_) {
    createToast('Network error', 'Unable to place the order right now.');
  }
}

function populateCategoryFilters() {
  const filterWrap = document.getElementById('categoryFilters');
  const cards = document.querySelectorAll('.product-card[data-category]');
  if (!filterWrap || !cards.length) return;

  const categories = [...new Set([...cards].map((card) => card.dataset.category))].sort();
  filterWrap.innerHTML = categories.map((category) => `
    <label class="checkbox-item filter-chip">
      <span>${category}</span>
      <input type="checkbox" class="category-filter" value="${category}" checked>
    </label>
  `).join('');
}

function applyFilters() {
  const searchEl = document.getElementById('searchInput');
  const minEl = document.getElementById('minPrice');
  const maxEl = document.getElementById('maxPrice');
  const inStockOnly = document.getElementById('inStockOnly');
  const cards = document.querySelectorAll('.product-card[data-category]');
  const selectedCategories = [...document.querySelectorAll('.category-filter:checked')].map((el) => el.value);
  const search = (searchEl?.value || '').trim().toLowerCase();
  const minPrice = Number(minEl?.value || 0);
  const maxPrice = Number(maxEl?.value || Number.POSITIVE_INFINITY);

  let visibleCount = 0;
  cards.forEach((card) => {
    const data = getProductData(card);
    const matchesSearch = !search || `${data.name} ${data.desc} ${data.category}`.toLowerCase().includes(search);
    const matchesCategory = !selectedCategories.length || selectedCategories.includes(data.category);
    const matchesPrice = data.price >= minPrice && data.price <= maxPrice;
    const matchesStock = !inStockOnly?.checked || data.stock > 0;
    const visible = matchesSearch && matchesCategory && matchesPrice && matchesStock;
    card.classList.toggle('hidden', !visible);
    if (visible) visibleCount += 1;
  });

  const noResults = document.getElementById('noResultsState');
  if (noResults) noResults.hidden = visibleCount !== 0;
}

function bindProductCards() {
  document.querySelectorAll('.product-card[data-slug]').forEach((card) => {
    const product = getProductData(card);
    card.querySelector('.add-to-cart-btn')?.addEventListener('click', () => addToCart(product));
  });
}

function bindDetailActions() {
  const detail = document.querySelector('[data-product-detail]');
  if (!detail) return;
  const product = getProductData(detail);
  document.getElementById('detailAddToCart')?.addEventListener('click', () => addToCart(product));
  document.getElementById('detailBuyNow')?.addEventListener('click', async () => {
    await addToCart(product);
    await placeOrder();
  });
}

function bindStaticEvents() {
  document.getElementById('cartIcon')?.addEventListener('click', openCartDrawer);
  document.getElementById('closeCartModal')?.addEventListener('click', closeCartDrawer);
  document.getElementById('cartViewOrdersBtn')?.addEventListener('click', () => {
    window.location.href = '/orders';
  });
  document.getElementById('cartPlaceOrderBtn')?.addEventListener('click', placeOrder);
  document.getElementById('cartPlaceOrderBtnPage')?.addEventListener('click', placeOrder);
  document.getElementById('orderStatusFilter')?.addEventListener('change', renderOrdersPage);

  document.getElementById('cartItemsList')?.addEventListener('click', async (event) => {
    const item = event.target.closest('[data-action]');
    const row = event.target.closest('[data-slug]');
    if (!item || !row) return;
    const { action } = item.dataset;
    const slug = row.dataset.slug;
    if (action === 'inc') await updateCartItem(slug, 1);
    if (action === 'dec') await updateCartItem(slug, -1);
    if (action === 'remove') await removeCartItem(slug);
  });

  document.getElementById('cartList')?.addEventListener('click', async (event) => {
    const actionEl = event.target.closest('[data-action]');
    const row = event.target.closest('[data-slug]');
    if (!actionEl || !row) return;
    const { action } = actionEl.dataset;
    const slug = row.dataset.slug;
    if (action === 'inc') await updateCartItem(slug, 1);
    if (action === 'dec') await updateCartItem(slug, -1);
    if (action === 'remove') await removeCartItem(slug);
  });

  document.getElementById('ordersList')?.addEventListener('click', (event) => {
    const button = event.target.closest('[data-order-id]');
    if (!button) return;
    openOrderDetail(button.dataset.orderId);
  });

  document.getElementById('recentOrdersBody')?.addEventListener('click', (event) => {
    const button = event.target.closest('[data-order-id]');
    if (!button) return;
    openOrderDetail(button.dataset.orderId);
  });

  document.querySelectorAll('[data-close-order-modal]').forEach((el) => {
    el.addEventListener('click', closeOrderDetail);
  });

  const searchInput = document.getElementById('searchInput');
  const minPrice = document.getElementById('minPrice');
  const maxPrice = document.getElementById('maxPrice');
  const inStockOnly = document.getElementById('inStockOnly');
  const applyBtn = document.querySelector('.filters-sidebar .btn-primary');
  const resetBtn = document.querySelector('.filter-reset');
  [searchInput, minPrice, maxPrice, inStockOnly].forEach((el) => {
    if (el?.type === 'checkbox') el.addEventListener('change', applyFilters);
    else if (el) el.addEventListener('input', applyFilters);
  });

  applyBtn?.addEventListener('click', applyFilters);
  resetBtn?.addEventListener('click', () => {
    if (searchInput) searchInput.value = '';
    if (minPrice) minPrice.value = '0';
    if (maxPrice) maxPrice.value = '';
    if (inStockOnly) inStockOnly.checked = false;
    document.querySelectorAll('.category-filter').forEach((el) => { el.checked = true; });
    applyFilters();
  });
}

document.addEventListener('DOMContentLoaded', async () => {
  populateCategoryFilters();
  bindProductCards();
  bindDetailActions();
  bindStaticEvents();
  await refreshCart();
  await refreshOrders();
  applyFilters();
});
