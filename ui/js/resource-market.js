import { htmlElement } from './dom-utils.js';

const SHARED_RESOURCE_PRICES = [1, 2, 3, 4, 5, 6, 7, 8];
const NUCLEAR_PRICES = [1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 14, 16];
const RESOURCE_RACKS = [
  { id: 'coal', label: 'Coal', icon: '🪨', capacity: 24, prices: SHARED_RESOURCE_PRICES, slotsPerTier: 3 },
  { id: 'oil', label: 'Oil', icon: '🛢️', capacity: 24, prices: SHARED_RESOURCE_PRICES, slotsPerTier: 3 },
  { id: 'trash', label: 'Garbage', icon: '🗑️', capacity: 24, prices: SHARED_RESOURCE_PRICES, slotsPerTier: 3 },
  { id: 'uranium', label: 'Nuclear', icon: '☢️', capacity: 12, prices: NUCLEAR_PRICES, slotsPerTier: 1 },
];

function createRack({ id, label, icon, capacity, prices, slotsPerTier }, available = 0) {
  const rack = htmlElement('section', {
    className: `resource-rack resource-${id}`,
    'aria-label': `${label}: ${available} available of ${capacity} spaces`,
    title: label,
  });
  const heading = htmlElement('div', { className: 'resource-rack-heading' });
  heading.appendChild(htmlElement('span', {
    className: 'resource-rack-icon',
    'aria-hidden': 'true',
    textContent: icon,
  }));
  rack.appendChild(heading);

  const slots = htmlElement('div', { className: 'resource-rack-slots' });
  slots.style.gridTemplateColumns = `repeat(${NUCLEAR_PRICES.length}, minmax(0, 1fr))`;
  for (let tierIndex = 0; tierIndex < NUCLEAR_PRICES.length; tierIndex += 1) {
    const tier = htmlElement('div', { className: 'resource-tier' });
    if (tierIndex >= prices.length) {
      tier.classList.add('resource-tier-empty');
      slots.appendChild(tier);
      continue;
    }
    const tierSlots = htmlElement('div', { className: 'resource-tier-slots' });
    for (let slotIndex = 0; slotIndex < slotsPerTier; slotIndex += 1) {
      const resourceIndex = tierIndex * slotsPerTier + slotIndex;
      if (resourceIndex >= capacity) break;
      tierSlots.appendChild(htmlElement('span', {
        className: `resource-slot${resourceIndex >= capacity - available ? ' filled' : ''}`,
        'aria-hidden': 'true',
      }));
    }
    tier.appendChild(tierSlots);
    slots.appendChild(tier);
  }
  rack.appendChild(slots);
  return rack;
}

function createPriceRack() {
  const rack = htmlElement('section', {
    className: 'resource-price-rack',
    'aria-label': 'Resource prices',
  });
  rack.appendChild(htmlElement('div', {
    className: 'resource-price-spacer',
    'aria-hidden': 'true',
  }));

  const slots = htmlElement('div', { className: 'resource-rack-slots' });
  slots.style.gridTemplateColumns = `repeat(${NUCLEAR_PRICES.length}, minmax(0, 1fr))`;
  NUCLEAR_PRICES.forEach((price) => {
    const tier = htmlElement('div', { className: 'resource-tier' });
    tier.appendChild(htmlElement('span', {
      className: 'resource-tier-price',
      textContent: price,
    }));
    slots.appendChild(tier);
  });
  rack.appendChild(slots);
  return rack;
}

export function initResourceMarket(gameState) {
  const market = document.getElementById('resource-market');
  market.replaceChildren(createPriceRack(), ...RESOURCE_RACKS.map((rack) => (
    createRack(rack, gameState.resource_market[rack.id])
  )));
}