document.addEventListener('DOMContentLoaded', () => {
  Chart.defaults.color = 'rgba(255,255,255,0.72)';
  Chart.defaults.font.family = 'Inter, system-ui, sans-serif';

  const chartDataEl = document.getElementById('dashboardChartData');
  const chartData = chartDataEl ? JSON.parse(chartDataEl.textContent || '{}') : {};

  const salesCtx = document.getElementById('salesChart');
  if (salesCtx && chartData.salesLabels?.length) {
    new Chart(salesCtx, {
      type: 'bar',
      data: {
        labels: chartData.salesLabels,
        datasets: [
          {
            label: 'Last Month Sales',
            data: chartData.lastMonthSales,
            backgroundColor: 'rgba(148, 163, 184, 0.45)',
            borderColor: 'rgba(148, 163, 184, 0.9)',
            borderWidth: 1,
            borderRadius: 8,
          },
          {
            label: 'Current Monthly Sales',
            data: chartData.monthlySales,
            backgroundColor: 'rgba(52, 211, 153, 0.72)',
            borderColor: '#34d399',
            borderWidth: 1,
            borderRadius: 8,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: { position: 'top', labels: { usePointStyle: true, boxWidth: 8 } },
          tooltip: { backgroundColor: '#10142f', borderColor: 'rgba(255,255,255,0.16)', borderWidth: 1 },
        },
        scales: {
          x: {
            grid: { display: false },
            ticks: { maxRotation: 35, minRotation: 0 },
          },
          y: {
            beginAtZero: true,
            title: { display: true, text: 'Units sold' },
            grid: { color: 'rgba(255,255,255,0.06)' },
          },
        },
      },
    });
  }

  const stockCtx = document.getElementById('categoryChart');
  if (stockCtx && chartData.stockStatusLabels?.length) {
    new Chart(stockCtx, {
      type: 'doughnut',
      data: {
        labels: chartData.stockStatusLabels,
        datasets: [{
          data: chartData.stockStatusValues,
          backgroundColor: ['#34d399', '#f59e0b', '#ef4444', '#64748b'],
          borderColor: 'rgba(10,14,39,0.95)',
          borderWidth: 4,
          hoverOffset: 12,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '58%',
        plugins: {
          legend: { position: 'top', labels: { usePointStyle: true, boxWidth: 8 } },
          tooltip: { backgroundColor: '#10142f', borderColor: 'rgba(255,255,255,0.16)', borderWidth: 1 },
        },
      },
    });
  }
});
