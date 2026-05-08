document.addEventListener('DOMContentLoaded', () => {
  const salesCtx = document.getElementById('salesChart');
  if (salesCtx) {
    fetch('/api/sales_series')
      .then((r) => r.json())
      .then((j) => {
        if (!j.ok) return;
        new Chart(salesCtx, {
          type: 'line',
          data: { labels: j.dates.slice(-30), datasets: [{ label: 'Sales', data: j.sales.slice(-30), borderColor: '#ff7a2a', backgroundColor: 'rgba(255,122,42,0.15)', tension: 0.35, fill: true }] },
          options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } },
        });
      });
  }

  const categoryCtx = document.getElementById('categoryChart');
  if (categoryCtx) {
    fetch('/api/category_share')
      .then((r) => r.json())
      .then((j) => {
        if (!j.ok) return;
        new Chart(categoryCtx, { type: 'pie', data: { labels: j.labels, datasets: [{ data: j.values, backgroundColor: ['#ff7a2a', '#ef4444', '#f59e0b', '#a855f7'], borderWidth: 0 }] }, options: { responsive: true, maintainAspectRatio: false } });
      });
  }
});
