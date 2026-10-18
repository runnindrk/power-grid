import { htmlElement } from './dom-utils.js';

export function renderMoneyCard(money) {
  const grid = htmlElement('div', { className: 'money-grid' });

  for (const row of money.rows) {
    const pair = htmlElement('div', { className: 'money-pair' });

    pair.append(
      htmlElement('span', { className: 'houses', textContent: row.houses }),
      htmlElement('span', { className: 'value', textContent: row.value }),
    );
    grid.appendChild(pair);
  }

  const card = htmlElement('div', { className: 'info-card money-card' });

  card.appendChild(grid);

  return card;
}
