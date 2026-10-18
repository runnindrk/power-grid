import { htmlElement } from './dom-utils.js';

function createTier(tier) {
  const element = htmlElement('div', { className: tier.classes });

  if (tier.empty) {
    return element;
  }

  const slots = htmlElement('div', { className: 'resource-tier-slots' });

  for (const slot of tier.slots) {
    slots.appendChild(htmlElement('span', { className: slot.classes, 'aria-hidden': 'true' }));
  }

  element.appendChild(slots);

  return element;
}

function createSlotsGrid(gridTemplateColumns) {
  const slots = htmlElement('div', { className: 'resource-rack-slots' });

  slots.style.gridTemplateColumns = gridTemplateColumns;

  return slots;
}

function createPriceRack(market) {
  const rack = htmlElement('section', { className: 'resource-price-rack', 'aria-label': 'Resource prices' });

  rack.appendChild(htmlElement('div', { className: 'resource-price-spacer', 'aria-hidden': 'true' }));

  const slots = createSlotsGrid(market.grid_template_columns);

  for (const price of market.price_row.prices) {
    const tier = htmlElement('div', { className: 'resource-tier' });

    tier.appendChild(htmlElement('span', { className: 'resource-tier-price', textContent: price }));
    slots.appendChild(tier);
  }

  rack.appendChild(slots);

  return rack;
}

function createRack(rack, gridTemplateColumns) {
  const element = htmlElement('section', {
    className: rack.classes,
    'aria-label': rack.aria_label,
    title: rack.title,
  });
  const heading = htmlElement('div', { className: 'resource-rack-heading' });

  heading.appendChild(htmlElement('span', {
    className: 'resource-rack-icon',
    'aria-hidden': 'true',
    textContent: rack.icon,
  }));
  element.appendChild(heading);

  const slots = createSlotsGrid(gridTemplateColumns);

  for (const tier of rack.tiers) {
    slots.appendChild(createTier(tier));
  }

  element.appendChild(slots);

  return element;
}

export function renderResourceMarket(market) {
  const container = document.getElementById('resource-market');

  container.replaceChildren(createPriceRack(market));

  for (const rack of market.racks) {
    container.appendChild(createRack(rack, market.grid_template_columns));
  }
}
