import { fetchMoneyData } from './data-source.js';
import { htmlElement } from './dom-utils.js';

function renderMoneyCard(moneyData) {
  const grid = htmlElement('div', { className: 'money-grid' });
  Object.entries(moneyData.money[0]).forEach(([houses, value]) => {
    const pair = htmlElement('div', { className: 'money-pair' });
    pair.append(
      htmlElement('span', { className: 'houses', textContent: parseInt(houses, 10) }),
      htmlElement('span', { className: 'value', textContent: value }),
    );
    grid.appendChild(pair);
  });

  const card = htmlElement('div', { className: 'info-card money-card' });
  card.appendChild(grid);
  return card;
}

export async function initMoneyCard(container) {
  container.appendChild(renderMoneyCard(await fetchMoneyData()));
}
