import { htmlElement } from './dom-utils.js';

const PLAYER_COLORS = ['#e85d5d', '#519cde', '#43a047', '#fb8c00'];
const RESOURCE_DETAILS = [
  ['coal', '🪨', 'Coal'],
  ['oil', '🛢️', 'Oil'],
  ['trash', '🗑️', 'Trash'],
  ['uranium', '☢️', 'Uranium'],
];

function countNetworkHouses(mapHouses, player) {
  return Object.values(mapHouses).reduce((count, citySpots) => (
    count + Object.values(citySpots).filter((owner) => owner === player).length
  ), 0);
}

function createPlantSlot(player, plantId, slotIndex) {
  const isEmpty = plantId === undefined || plantId === null;
  const slot = htmlElement('div', {
    className: `player-plant-slot${isEmpty ? ' empty' : ''}`,
    'aria-label': isEmpty
      ? `Empty power plant slot ${slotIndex + 1} for ${player}`
      : `Power plant ${plantId} owned by ${player}`,
  });
  slot.appendChild(htmlElement('span', {
    className: isEmpty ? 'empty-slot-label' : 'player-plant-number',
    textContent: isEmpty ? 'Empty' : plantId,
  }));
  return slot;
}

function createResourceList(resources) {
  const list = htmlElement('div', { className: 'player-resources' });
  RESOURCE_DETAILS.forEach(([resource, icon, label]) => {
    const item = htmlElement('span', {
      className: `player-resource resource-${resource}`,
      title: label,
      'aria-label': `${resources[resource] ?? 0} ${label}`,
    });
    item.append(
      htmlElement('span', { className: 'player-resource-icon', 'aria-hidden': 'true', textContent: icon }),
      htmlElement('span', { textContent: resources[resource] ?? 0 }),
    );
    list.appendChild(item);
  });
  return list;
}

function createPlayerRow(player, index, gameState) {
  const row = htmlElement('article', {
    className: 'player-row',
    'aria-label': `Player ${player}`,
  });
  row.style.setProperty('--player-color', PLAYER_COLORS[index % PLAYER_COLORS.length]);

  const plants = gameState.player_power_plants[player] || [];
  const info = htmlElement('div', { className: 'player-info' });
  const heading = htmlElement('div', { className: 'player-info-heading' });
  heading.append(
    htmlElement('span', { className: 'player-name', textContent: player }),
    htmlElement('span', { className: 'player-money', textContent: `$${gameState.player_money[player] ?? 0}` }),
  );
  const network = htmlElement('div', { className: 'player-network' });
  network.append(
    htmlElement('span', { className: 'network-count', textContent: countNetworkHouses(gameState.map_houses, player) }),
    htmlElement('span', { className: 'network-label', textContent: 'in network' }),
  );
  info.append(heading, network, createResourceList(gameState.player_resources[player] || {}));
  row.appendChild(info);

  for (let slot = 0; slot < 3; slot += 1) {
    row.appendChild(createPlantSlot(player, plants[slot], slot));
  }
  return row;
}

export function updatePlayerBoard(gameState) {
  const players = gameState.player_turn_order.slice(0, 2);
  const rows = players.map((player, index) => createPlayerRow(player, index, gameState));
  document.getElementById('player-board').replaceChildren(...rows);
}

export const initPlayerBoard = updatePlayerBoard;