import { htmlElement } from './dom-utils.js';
import { fetchJson } from './data-source.js';

const PLANT_DECK_URL = '../../game_info/static_info/power_grid_deck_set_0.json';
const FUEL_TYPES = [
  ['coal', '🪨', 'Coal'],
  ['oil', '🛢️', 'Oil'],
  ['trash', '🗑️', 'Trash'],
  ['gas', '🔥', 'Gas'],
  ['uranium', '☢️', 'Uranium'],
];

function createFuelDisplay(plant) {
  const fuels = FUEL_TYPES
    .filter(([resource]) => plant[resource] > 0)
    .map(([resource, icon, label]) => ({ resource, icon, label, amount: plant[resource] }));
  const container = htmlElement('div', { className: 'plant-fuels' });

  if (fuels.length === 0) {
    container.appendChild(htmlElement('span', { className: 'plant-no-fuel', textContent: 'No fuel' }));
    return container;
  }

  const options = htmlElement('div', { className: `fuel-options${plant.hybrid ? ' hybrid' : ''}` });
  fuels.forEach((fuel, index) => {
    if (index > 0) {
      options.appendChild(htmlElement('span', {
        className: 'fuel-join',
        textContent: plant.hybrid ? 'or' : '+',
      }));
    }
    const item = htmlElement('span', {
      className: `fuel-item fuel-${fuel.resource}`,
      title: fuel.label,
      'aria-label': `${fuel.amount} ${fuel.label}`,
    });
    item.append(
      htmlElement('span', { className: 'fuel-icon', textContent: fuel.icon }),
      htmlElement('span', { className: 'fuel-amount', textContent: fuel.amount }),
    );
    options.appendChild(item);
  });
  container.appendChild(options);
  return container;
}

function createPlantStorage(plant, resources = {}, playerId, plantId) {
  const fuelAmounts = FUEL_TYPES
    .map(([resource]) => plant[resource] ?? 0)
    .filter((amount) => amount > 0);
  const fuelAmount = plant.hybrid
    ? Math.max(...fuelAmounts)
    : fuelAmounts.reduce((total, amount) => total + amount, 0);
  const capacity = fuelAmount * 2;
  if (capacity === 0) return null;

  const storedResources = Object.entries(resources)
    .flatMap(([resource, amount]) => Array.from(
      { length: Math.max(0, Math.floor(amount)) },
      () => resource,
    ))
    .slice(0, capacity);
  const storage = htmlElement('div', {
    className: 'plant-storage',
    'aria-label': `${capacity} resource storage spaces`,
  });

  for (let slot = 0; slot < capacity; slot += 1) {
    const resource = storedResources[slot];
    const fuel = FUEL_TYPES.find(([fuelType]) => fuelType === resource);
    storage.appendChild(htmlElement('span', {
      className: `plant-storage-slot${resource ? ` filled fuel-${resource}` : ''}`,
      draggable: resource ? 'true' : 'false',
      'data-player-id': playerId,
      'data-plant-id': plantId,
      'data-slot-index': slot,
      title: resource ? `${fuel?.[2] ?? resource} stored` : 'Empty storage space',
      'aria-label': resource ? `${fuel?.[2] ?? resource} stored` : 'Empty storage space',
    }));
  }

  return storage;
}

export function createPlantCard(plantId, plant, playerOwned = false, resources = {}, playerId) {
  const card = htmlElement('article', {
    className: `power-plant-card${plant?.special ? ' special' : ''}${playerOwned ? ' player-owned-plant' : ''}`,
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
  if (playerOwned) {
    const storage = createPlantStorage(plant, resources, playerId, plantId);
    if (storage) {
      const fuelStorage = htmlElement('div', { className: 'plant-fuel-storage' });
      fuelStorage.append(createFuelDisplay(plant), storage);
      card.appendChild(fuelStorage);
    } else {
      card.appendChild(createFuelDisplay(plant));
    }
  } else {
    card.appendChild(createFuelDisplay(plant));
  }
  return card;
}

export async function initPowerPlantMarket(gameState) {
  const { deck } = await fetchJson(PLANT_DECK_URL);
  const plantsById = new Map(deck.map((plant) => [plant.cost, plant]));
  const marketIds = gameState.power_plant_market;
  const market = document.getElementById('power-plant-market');
  const grid = market.querySelector('.power-plant-grid');

  grid.replaceChildren(...marketIds.map((plantId) => createPlantCard(plantId, plantsById.get(plantId))));
  return plantsById;
}