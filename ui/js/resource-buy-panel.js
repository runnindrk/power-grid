import { htmlElement } from './dom-utils.js';
import { requestBuyResources, requestResourcePrice } from './game-api.js';

const BUYABLE_RESOURCES = [
  ['coal', 'Coal'],
  ['oil', 'Oil'],
  ['trash', 'Trash'],
  ['uranium', 'Nuclear'],
];

export function createResourceBuyPanel(player, playerAlias) {
  const panel = htmlElement('form', {
    className: 'player-resource-buy-panel',
    'aria-label': `Buy resources for ${playerAlias}`,
  });
  const quantities = [];
  const options = htmlElement('div', { className: 'resource-buy-options' });
  BUYABLE_RESOURCES.forEach(([resource, label]) => {
    const row = htmlElement('label', { className: `resource-buy-row resource-${resource}` });
    const input = htmlElement('input', {
      className: 'resource-buy-quantity',
      type: 'number',
      value: '0',
      'aria-label': `${label} quantity for ${playerAlias}`,
    });
    row.append(
      htmlElement('span', { className: 'resource-buy-name', textContent: label }),
      input,
    );
    options.appendChild(row);
    quantities.push({ resource, input });
  });

  const buyPrice = htmlElement('span', { className: 'resource-buy-total', textContent: '$0' });
  const buyButton = htmlElement('button', {
    className: 'resource-buy-button',
    type: 'submit',
    'aria-label': `Buy selected resources for ${playerAlias}`,
  });
  buyButton.append(htmlElement('span', { className: 'resource-buy-label', textContent: 'Buy' }), buyPrice);
  panel.append(options, buyButton);

  let quoteRequestId = 0;

  const getResources = () => Object.fromEntries(quantities.map(({ resource, input }) => [
    resource,
    input.value === '' ? 0 : input.valueAsNumber,
  ]));

  async function updateQuote() {
    const requestId = ++quoteRequestId;
    try {
      const result = await requestResourcePrice(player, getResources());
      if (requestId === quoteRequestId) buyPrice.textContent = `$${result.price}`;
    } catch (error) {
      console.error(error);
    }
  }

  quantities.forEach(({ input }) => input.addEventListener('input', updateQuote));

  panel.addEventListener('submit', async (event) => {
    event.preventDefault();
    try {
      const result = await requestBuyResources(player, getResources());
      buyPrice.textContent = `$${result.price}`;
    } catch (error) {
      console.error(error);
    }
  });
  return panel;
}
