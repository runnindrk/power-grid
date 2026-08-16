const MONEY_DATA_URL = '../../game_info/static_info/power_grid_money.json';

function renderMoneyCard(moneyData) {
  const entries = Object.entries(moneyData.money[0]);

  const card = document.createElement('div');
  card.className = 'info-card money-card';

  const grid = document.createElement('div');
  grid.className = 'money-grid';
  entries.forEach(([key, value]) => {
    const houses = parseInt(key, 10);
    const pair = document.createElement('div');
    pair.className = 'money-pair';
    pair.innerHTML = `<span class="houses">${houses}</span><span class="value">${value}</span>`;
    grid.appendChild(pair);
  });
  card.appendChild(grid);
  return card;
}

export async function initMoneyCard(container) {
  const res = await fetch(MONEY_DATA_URL);
  const moneyData = await res.json();
  container.appendChild(renderMoneyCard(moneyData));
}
