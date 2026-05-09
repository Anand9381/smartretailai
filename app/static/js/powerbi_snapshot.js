document.addEventListener('DOMContentLoaded', () => {
  const dataEl = document.getElementById('powerbiSnapshotData');
  if (!dataEl || typeof Chart === 'undefined') return;

  const data = JSON.parse(dataEl.textContent || '{}');
  Chart.defaults.color = '#4b5563';
  Chart.defaults.font.family = 'Inter, system-ui, sans-serif';

  const lineCtx = document.getElementById('pbiLineChart');
  if (lineCtx) {
    new Chart(lineCtx, {
      type: 'line',
      data: {
        labels: data.labels || [],
        datasets: [
          {
            label: 'Sum of predictedFutureSales',
            data: data.predictedFutureSales || [],
            borderColor: '#1d8cf8',
            backgroundColor: '#1d8cf8',
            pointRadius: 4,
            tension: 0.25,
          },
          {
            label: 'Sum of monthlySales',
            data: data.monthlySales || [],
            borderColor: '#18259b',
            backgroundColor: '#18259b',
            pointRadius: 4,
            tension: 0.25,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: 'top', align: 'start', labels: { usePointStyle: true } } },
        scales: {
          x: { ticks: { maxRotation: 38, minRotation: 25 }, grid: { display: false }, title: { display: true, text: 'name' } },
          y: { beginAtZero: true, grid: { color: 'rgba(0,0,0,0.12)', borderDash: [2, 4] } },
        },
      },
    });
  }

  const donutCtx = document.getElementById('pbiStockRiskChart');
  if (donutCtx) {
    new Chart(donutCtx, {
      type: 'doughnut',
      data: {
        labels: data.stockRiskLabels || [],
        datasets: [{
          data: data.stockRiskValues || [],
          backgroundColor: ['#1d8cf8', '#1f2aa5', '#e16a3a'],
          borderColor: '#ffffff',
          borderWidth: 2,
          hoverOffset: 10,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '58%',
        plugins: { legend: { position: 'right', labels: { usePointStyle: true } } },
      },
    });
  }

  const scatterCtx = document.getElementById('pbiScatterChart');
  if (scatterCtx) {
    const grouped = {};
    (data.scatterPoints || []).forEach((point) => {
      grouped[point.category] ||= [];
      grouped[point.category].push(point);
    });
    const colors = ['#1d8cf8', '#18259b', '#e2763d', '#8626a4', '#d94ea8', '#16a34a'];
    new Chart(scatterCtx, {
      type: 'bubble',
      data: {
        datasets: Object.entries(grouped).map(([category, points], index) => ({
          label: category,
          data: points.map((point) => ({ x: point.x, y: point.y, r: point.r, name: point.name })),
          backgroundColor: colors[index % colors.length],
        })),
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'top', align: 'start', labels: { usePointStyle: true } },
          tooltip: {
            callbacks: {
              label(context) {
                const raw = context.raw;
                return `${raw.name}: monthly ${raw.x}, predicted ${raw.y}`;
              },
            },
          },
        },
        scales: {
          x: { title: { display: true, text: 'Sum of monthlySales' }, beginAtZero: true, grid: { color: 'rgba(0,0,0,0.12)', borderDash: [2, 4] } },
          y: { title: { display: true, text: 'Sum of predictedFutureSales' }, beginAtZero: true, grid: { color: 'rgba(0,0,0,0.12)', borderDash: [2, 4] } },
        },
      },
    });
  }
});
