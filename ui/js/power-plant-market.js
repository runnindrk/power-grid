import { htmlElement } from './dom-utils.js';
import { fetchPlantDeck } from './data-source.js';
import { RESOURCE_ICONS } from './resource-icons.js';

const FUEL_LABELS = { coal: 'Coal', oil: 'Oil', trash: 'Trash', gas: 'Gas', uranium: 'Uranium' };
const FUEL_TYPES = Object.keys(FUEL_LABELS);

function requiredFuels(plant) {
  return FUEL_TYPES
    .filter((resource) => plant[resource] > 0)
    .map((resource) => ({ resource, label: FUEL_LABELS[resource], amount: plant[resource] }));
}

// A plant stores up to twice the fuel it burns per round.
function storageCapacity(plant) {
  const amounts = requiredFuels(plant).map(({ amount }) => amount);
  if (amounts.length === 0) return 0;
  const fuelAmount = plant.hybrid ? Math.max(...amounts) : amounts.reduce((total, amount) => total + amount, 0);
  return fuelAmount * 2;
}

function createFuelDisplay(plant) {
  const fuels = requiredFuels(plant);
  const container = htmlElement('div', { className: 'plant-fuels' });

  if (fuels.length === 0) {
    container.appendChild(htmlElement('span', { className: 'plant-no-fuel', textContent: 'No fuel' }));
    return container;
  }

  const options = htmlElement('div', { className: `fuel-options${plant.hybrid ? ' hybrid' : ''}` });
  fuels.forEach(({ resource, label, amount }, index) => {
    if (index > 0) {
      options.appendChild(htmlElement('span', {
        className: 'fuel-join',
        textContent: plant.hybrid ? 'or' : '+',
      }));
    }
    const item = htmlElement('span', {
      className: `fuel-item fuel-${resource}`,
      title: label,
      'aria-label': `${amount} ${label}`,
    });
    item.append(
      htmlElement('span', { className: 'fuel-icon', textContent: RESOURCE_ICONS[resource] }),
      htmlElement('span', { className: 'fuel-amount', textContent: amount }),
    );
    options.appendChild(item);
  });
  container.appendChild(options);
  return container;
}

function createPlantStorage(plant, { playerId, resources = {} }, plantId) {
  const capacity = storageCapacity(plant);
  if (capacity === 0) return null;

  const storedResources = Object.entries(resources)
    .flatMap(([resource, amount]) => Array(Math.max(0, Math.floor(amount))).fill(resource))
    .slice(0, capacity);
  const storage = htmlElement('div', {
    className: 'plant-storage',
    'aria-label': `${capacity} resource storage spaces`,
  });

  for (let slot = 0; slot < capacity; slot += 1) {
    const resource = storedResources[slot];
    const description = resource ? `${FUEL_LABELS[resource] ?? resource} stored` : 'Empty storage space';
    storage.appendChild(htmlElement('span', {
      className: `plant-storage-slot${resource ? ` filled fuel-${resource}` : ''}`,
      draggable: resource ? 'true' : 'false',
      'data-player-id': playerId,
      'data-plant-id': plantId,
      'data-slot-index': slot,
      title: description,
      'aria-label': description,
    }));
  }
  return storage;
}

// `owner` ({ playerId, resources }) is set only for plants on a player board, which show their storage.
export function createPlantCard(plantId, plant, owner = null) {
  const card = htmlElement('article', {
    className: `power-plant-card${plant?.special ? ' special' : ''}${owner ? ' player-owned-plant' : ''}`,
    'data-plant-id': plantId,
    'aria-label': plant
      ? `Power plant ${plantId}, powers ${plant.houses} cities`
      : `Power plant ${plantId}, details unavailable`,
  });
  const heading = htmlElement('div', { className: 'plant-heading' });
  heading.append(
    htmlElement('span', { className: 'plant-number', textContent: plantId }),
    htmlElement('span', { className: 'plant-kind', textContent: plant?.special ? 'Special' : 'Plant' }),
  );
  card.appendChild(heading);

  if (!plant) {
    card.appendChild(htmlElement('p', { className: 'plant-unavailable', textContent: 'Details unavailable' }));
    return card;
  }

  const output = htmlElement('div', { className: 'plant-output' });
  output.append(
    htmlElement('span', { className: 'output-icon', 'aria-hidden': 'true', textContent: '⌂' }),
    htmlElement('span', { className: 'output-count', textContent: plant.houses }),
    htmlElement('span', { className: 'output-label', textContent: 'cities' }),
  );
  card.appendChild(output);

  const storage = owner && createPlantStorage(plant, owner, plantId);
  if (storage) {
    const fuelStorage = htmlElement('div', { className: 'plant-fuel-storage' });
    fuelStorage.append(createFuelDisplay(plant), storage);
    card.appendChild(fuelStorage);
  } else {
    card.appendChild(createFuelDisplay(plant));
  }
  return card;
}

export async function initPowerPlantMarket(gameState) {
  const { deck } = await fetchPlantDeck();
  const plantsById = new Map(deck.map((plant) => [plant.cost, plant]));
  const grid = document.querySelector('#power-plant-market .power-plant-grid');

  grid.replaceChildren(...gameState.power_plant_market.map((plantId) => createPlantCard(plantId, plantsById.get(plantId))));
  return plantsById;
}
