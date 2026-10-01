import { fetchJson } from './data-source.js';
import { htmlElement } from './dom-utils.js';

const MONEY_DATA_URL = '../../game_info/static_info/power_grid_money.json';

function renderMoneyCard(moneyData) {
  const entries = Object.entries(moneyData.money[0]);

  const card = htmlElement('div', { className: 'info-card money-card' });
  const grid = htmlElement('div', { className: 'money-grid' });
  entries.forEach(([key, value]) => {
    const houses = parseInt(key, 10);
    const pair = htmlElement('div', { className: 'money-pair' });
    pair.append(
      htmlElement('span', { className: 'houses', textContent: houses }),
      htmlElement('span', { className: 'value', textContent: value }),
    );
    grid.appendChild(pair);
  });
  card.appendChild(grid);
  return card;
}

export async function initMoneyCard(container) {
  container.appendChild(renderMoneyCard(await fetchJson(MONEY_DATA_URL)));
}
