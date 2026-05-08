document.addEventListener('DOMContentLoaded', async () => {
  // Load forecast data when page loads
  await loadForecastData();
  
  // Set up auto-refresh every 30 seconds
  setInterval(loadForecastData, 30000);
});

async function loadForecastData() {
  try {
    const response = await fetch('/api/admin/forecast-data');
    if (!response.ok) {
      console.error('Failed to fetch forecast data:', response.status);
      return;
    }
    
    const data = await response.json();
    console.log('Forecast data loaded:', data);
    
    // Update charts if they exist
    if (document.getElementById('demandLineChart')) {
      renderLineChart(data);
    }
    if (document.getElementById('correlationScatterPlot')) {
      renderScatterPlot(data);
    }
    if (document.getElementById('productGrowthCards')) {
      renderGrowthCards(data);
    }
    if (document.getElementById('aiInsights')) {
      renderInsights(data);
    }
  } catch (error) {
    console.error('Error loading forecast data:', error);
  }
}

function renderLineChart(data) {
  const ctx = document.getElementById('demandLineChart');
  if (!ctx) return;
  
  const ctxElement = ctx.getContext('2d');
  
  // Destroy existing chart if any
  if (window.demandChart) {
    window.demandChart.destroy();
  }
  
  window.demandChart = new Chart(ctxElement, {
    type: 'line',
    data: {
      labels: data.map(p => p.name),
      datasets: [
        {
          label: 'Current Monthly Sales',
          data: data.map(p => p.monthlySales),
          borderColor: '#ff7b2f',
          backgroundColor: 'rgba(255, 123, 47, 0.1)',
          borderWidth: 3,
          tension: 0.4,
          fill: true,
          pointBackgroundColor: '#ff7b2f',
          pointBorderColor: '#fff',
          pointRadius: 4
        },
        {
          label: 'Predicted Future Sales',
          data: data.map(p => p.predictedFutureSales),
          borderColor: '#2fff7b',
          backgroundColor: 'rgba(47, 255, 123, 0.1)',
          borderWidth: 3,
          borderDash: [5, 5],
          tension: 0.4,
          fill: true,
          pointBackgroundColor: '#2fff7b',
          pointBorderColor: '#fff',
          pointRadius: 4
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: true,
          labels: {
            color: 'rgba(255, 255, 255, 0.7)',
            font: { size: 12 }
          }
        },
        tooltip: {
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          titleColor: '#fff',
          bodyColor: '#fff'
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: { color: 'rgba(255, 255, 255, 0.6)' }
        },
        x: {
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: { color: 'rgba(255, 255, 255, 0.6)' }
        }
      }
    }
  });
}

function renderScatterPlot(data) {
  const ctx = document.getElementById('correlationScatterPlot');
  if (!ctx) return;
  
  const ctxElement = ctx.getContext('2d');
  
  // Destroy existing chart if any
  if (window.correlationChart) {
    window.correlationChart.destroy();
  }
  
  // Create scatter data
  const scatterData = data.map((p, i) => ({
    x: p.monthlySales,
    y: p.predictedFutureSales,
    label: p.name
  }));
  
  window.correlationChart = new Chart(ctxElement, {
    type: 'scatter',
    data: {
      datasets: [
        {
          label: 'Demand Correlation',
          data: scatterData,
          backgroundColor: 'rgba(255, 123, 47, 0.6)',
          borderColor: '#ff7b2f',
          borderWidth: 2,
          pointRadius: 6,
          pointHoverRadius: 8
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: true,
          labels: { color: 'rgba(255, 255, 255, 0.7)' }
        },
        tooltip: {
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          titleColor: '#fff',
          bodyColor: '#fff',
          callbacks: {
            label: function(context) {
              return `${scatterData[context.dataIndex].label}`;
            }
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          title: { display: true, text: 'Predicted Sales', color: '#fff' },
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: { color: 'rgba(255, 255, 255, 0.6)' }
        },
        x: {
          title: { display: true, text: 'Current Sales', color: '#fff' },
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: { color: 'rgba(255, 255, 255, 0.6)' }
        }
      }
    }
  });
}

function renderGrowthCards(data) {
  const container = document.getElementById('productGrowthCards');
  if (!container) return;
  
  container.innerHTML = '';
  
  data.forEach(p => {
    const growth = ((p.predictedFutureSales - p.monthlySales) / p.monthlySales * 100).toFixed(1);
    const isPositive = parseFloat(growth) >= 0;
    
    const card = document.createElement('div');
    card.className = 'glass-card product-card';
    card.innerHTML = `
      <div class="product-header">
        <div>
          <h3 style="margin: 0 0 0.5rem; color: #fff; font-size: 1.1rem;">${p.name}</h3>
          <span class="badge-ai">AI FORECAST</span>
        </div>
      </div>
      <div class="growth-value ${isPositive ? 'growth-positive' : 'growth-negative'}">
        ${isPositive ? '+' : ''}${growth}%
      </div>
      <p style="font-size: 0.8rem; color: rgba(255, 255, 255, 0.5);">Growth Projection</p>
      <div class="progress-container">
        <div class="progress-bar" style="width: ${Math.min(Math.max(50 + parseFloat(growth), 10), 100)}%; background: ${isPositive ? 'var(--neon-green)' : 'var(--neon-red)'}; box-shadow: 0 0 10px ${isPositive ? 'var(--neon-green)' : 'var(--neon-red)'};"></div>
      </div>
      <div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: rgba(255, 255, 255, 0.4);">
        <span>Current: ${p.monthlySales}</span>
        <span>Next Target: ${p.predictedFutureSales}</span>
      </div>
    `;
    container.appendChild(card);
  });
}

function renderInsights(data) {
  const container = document.getElementById('aiInsights');
  if (!container) return;
  
  container.innerHTML = '';
  
  data.forEach((p, index) => {
    const growth = ((p.predictedFutureSales - p.monthlySales) / p.monthlySales * 100);
    let insightText = '';
    let icon = '';
    
    if (growth > 10) {
      insightText = `${p.name} expected demand increase next month. Scaling inventory recommended.`;
      icon = '🚀';
    } else if (growth < -5) {
      insightText = `${p.name} showing potential decline. Optimize stock levels and consider promotions.`;
      icon = '📉';
    } else {
      insightText = `${p.name} showing stable future demand. Maintain current inventory levels.`;
      icon = '💎';
    }

    const card = document.createElement('div');
    card.className = 'insight-card';
    card.style.animationDelay = `${index * 0.1}s`;
    card.innerHTML = `
      <div class="insight-icon">${icon}</div>
      <p style="font-weight: 500; font-size: 0.9rem; line-height: 1.4;">${insightText}</p>
    `;
    container.appendChild(card);
  });
}
