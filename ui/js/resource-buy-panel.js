import { htmlElement } from './dom-utils.js';
import { fetchView, postBuyResources, postResourcePrice } from './api.js';
import { renderResourceMarket } from './resource-market.js';

export function createResourceBuyPanel(player, refresh) {
  const buy = player.resource_buy;
  const panel = htmlElement('form', {
    className: 'player-resource-buy-panel',
    'aria-label': buy.aria_label,
  });

  const inputs = {};
  const options = htmlElement('div', { className: 'resource-buy-options' });

  for (const row of buy.rows) {
    const input = htmlElement('input', {
      className: 'resource-buy-quantity',
      type: 'number',
      min: '0',
      step: '1',
      value: String(row.quantity),
      'aria-label': row.aria_label,
    });
    input.disabled = buy.disabled;
    const label = htmlElement('label', { className: row.classes });

    label.append(
      htmlElement('span', {
        className: 'resource-buy-icon',
        title: row.label,
        textContent: row.icon,
      }),
      input,
    );
    options.appendChild(label);
    inputs[row.resource] = input;
  }

  const total = htmlElement('span', {
    className: 'resource-buy-total',
    textContent: buy.price_label,
  });
  const buyButton = htmlElement('button', {
    className: 'resource-buy-button',
    type: 'submit',
    'aria-label': buy.buy_aria_label,
  });

  buyButton.append(
    htmlElement('span', { className: 'resource-buy-label', textContent: buy.buy_label }),
    total,
  );
  buyButton.disabled = buy.disabled;
  panel.append(options, buyButton);

  // Keep entered values intact; the backend owns purchase validation and parsing.
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

    if (result.status === 'ok') {
      const view = await fetchView();

      renderResourceMarket(view.resource_market);
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
