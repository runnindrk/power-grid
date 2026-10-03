import { htmlElement } from './dom-utils.js';
import { RESOURCE_ICONS } from './resource-icons.js';

const SHARED_RESOURCE_PRICES = [1, 2, 3, 4, 5, 6, 7, 8];
const NUCLEAR_PRICES = [1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 14, 16];
const RESOURCE_RACKS = [
  { id: 'coal', label: 'Coal', capacity: 24, prices: SHARED_RESOURCE_PRICES, slotsPerTier: 3 },
  { id: 'oil', label: 'Oil', capacity: 24, prices: SHARED_RESOURCE_PRICES, slotsPerTier: 3 },
  { id: 'trash', label: 'Garbage', capacity: 24, prices: SHARED_RESOURCE_PRICES, slotsPerTier: 3 },
  { id: 'uranium', label: 'Nuclear', capacity: 12, prices: NUCLEAR_PRICES, slotsPerTier: 1 },
];

// Every rack is laid out on the widest (nuclear) price scale so tiers line up vertically.
function createSlotsGrid() {
  const slots = htmlElement('div', { className: 'resource-rack-slots' });
  slots.style.gridTemplateColumns = `repeat(${NUCLEAR_PRICES.length}, minmax(0, 1fr))`;
  return slots;
}

function createTier({ tierIndex, prices, slotsPerTier, capacity, available }) {
  const tier = htmlElement('div', { className: 'resource-tier' });
  if (tierIndex >= prices.length) {
    tier.classList.add('resource-tier-empty');
    return tier;
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
  return tier;
}

function createRack({ id, label, capacity, prices, slotsPerTier }, available = 0) {
  const rack = htmlElement('section', {
    className: `resource-rack resource-${id}`,
    'aria-label': `${label}: ${available} available of ${capacity} spaces`,
    title: label,
  });
  const heading = htmlElement('div', { className: 'resource-rack-heading' });
  heading.appendChild(htmlElement('span', {
    className: 'resource-rack-icon',
    'aria-hidden': 'true',
    textContent: RESOURCE_ICONS[id],
  }));
  rack.appendChild(heading);

  const slots = createSlotsGrid();
  for (let tierIndex = 0; tierIndex < NUCLEAR_PRICES.length; tierIndex += 1) {
    slots.appendChild(createTier({ tierIndex, prices, slotsPerTier, capacity, available }));
  }
  rack.appendChild(slots);
  return rack;
}

function createPriceRack() {
  const rack = htmlElement('section', {
    className: 'resource-price-rack',
    'aria-label': 'Resource prices',
  });
  rack.appendChild(htmlElement('div', { className: 'resource-price-spacer', 'aria-hidden': 'true' }));

  const slots = createSlotsGrid();
  NUCLEAR_PRICES.forEach((price) => {
    const tier = htmlElement('div', { className: 'resource-tier' });
    tier.appendChild(htmlElement('span', { className: 'resource-tier-price', textContent: price }));
    slots.appendChild(tier);
  });
  rack.appendChild(slots);
  return rack;
}

export function initResourceMarket(gameState) {
  document.getElementById('resource-market').replaceChildren(
    createPriceRack(),
    ...RESOURCE_RACKS.map((rack) => createRack(rack, gameState.resource_market[rack.id])),
  );
}
