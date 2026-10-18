import { htmlElement } from './dom-utils.js';
import { postBuyResources, postResourcePrice } from './api.js';

export function createResourceBuyPanel(player, refresh) {
  const buy = player.resource_buy;
  const panel = htmlElement('form', { className: 'player-resource-buy-panel', 'aria-label': buy.aria_label });

  const inputs = {};
  const options = htmlElement('div', { className: 'resource-buy-options' });

  for (const row of buy.rows) {
    const input = htmlElement('input', {
      className: 'resource-buy-quantity',
      type: 'number',
      value: '0',
      'aria-label': row.aria_label,
    });
    const label = htmlElement('label', { className: row.classes });

    label.append(htmlElement('span', { className: 'resource-buy-name', textContent: row.label }), input);
    options.appendChild(label);
    inputs[row.resource] = input;
  }

  const total = htmlElement('span', { className: 'resource-buy-total', textContent: buy.price_label });
  const buyButton = htmlElement('button', {
    className: 'resource-buy-button',
    type: 'submit',
    'aria-label': buy.buy_aria_label,
  });

  buyButton.append(htmlElement('span', { className: 'resource-buy-label', textContent: 'Buy' }), total);
  panel.append(options, buyButton);

  // The typed amounts are sent as they are; the backend decides what they mean.
  function typedQuantities() {
    const quantities = {};

    for (const resource in inputs) {
      quantities[resource] = inputs[resource].value;
    }

    return quantities;
  }

  async function showPrice() {
    const result = await postResourcePrice(player.player, typedQuantities());

    if (result.price_label) {
      total.textContent = result.price_label;
    }
  }

  for (const resource in inputs) {
    inputs[resource].addEventListener('input', showPrice);
  }

  panel.addEventListener('submit', (event) => {
    event.preventDefault();

    postBuyResources(player.player, typedQuantities()).then(refresh);
  });

  return panel;
}
