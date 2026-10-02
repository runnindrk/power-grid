import { htmlElement } from './dom-utils.js';

const PLAYER_COLORS = ['#e85d5d', '#519cde', '#43a047', '#fb8c00', '#9445aa', '#fdd835'];
const RESOURCE_DETAILS = [
  ['coal', 'Coal'],
  ['oil', 'Oil'],
  ['trash', 'Trash'],
  ['uranium', 'Uranium'],
];

function countNetworkHouses(mapHouses, player) {
  return Object.values(mapHouses).reduce((count, citySpots) => (
    count + Object.values(citySpots).filter((owner) => owner === player).length
  ), 0);
}

function createPlantSlot(playerAlias, plantId, slotIndex) {
  const isEmpty = plantId === undefined || plantId === null;
  const slot = htmlElement('div', {
    className: `player-plant-slot${isEmpty ? ' empty' : ''}`,
    'aria-label': isEmpty
      ? `Empty power plant slot ${slotIndex + 1} for ${playerAlias}`
      : `Power plant ${plantId} owned by ${playerAlias}`,
  });
  slot.appendChild(htmlElement('span', {
    className: isEmpty ? 'empty-slot-label' : 'player-plant-number',
    textContent: isEmpty ? 'Empty' : plantId,
  }));
  return slot;
}

function createResourceList(resources) {
  const list = htmlElement('div', { className: 'player-resources' });
  RESOURCE_DETAILS.forEach(([resource, label]) => {
    const item = htmlElement('span', {
      className: `player-resource resource-${resource}`,
      title: label,
      'aria-label': `${resources[resource] ?? 0} ${label}`,
      textContent: `${label} ${resources[resource] ?? 0}`,
    });
    list.appendChild(item);
  });
  return list;
}

function createBidPanel(playerAlias, money) {
  const panel = htmlElement('form', {
    className: 'player-bid-panel',
    'aria-label': `Power plant bid for ${playerAlias}`,
  });
  const label = htmlElement('label', { className: 'bid-field' });
  label.append(
    htmlElement('span', { textContent: 'Bid $' }),
  );
  const input = htmlElement('input', {
    className: 'bid-amount',
    type: 'number',
    min: '1',
    max: String(money),
    step: '1',
    value: '1',
    required: 'required',
    'aria-label': `Bid amount for ${playerAlias}`,
  });
  label.appendChild(input);

  const bidButton = htmlElement('button', {
    className: 'bid-submit',
    type: 'submit',
    textContent: 'Bid',
  });
  const passButton = htmlElement('button', {
    className: 'bid-pass',
    type: 'button',
    textContent: 'Go out',
  });
  const status = htmlElement('span', {
    className: 'bid-status',
    'aria-live': 'polite',
    textContent: 'No bid yet',
  });
  panel.append(label, bidButton, passButton, status);

  let currentBid = 0;
  panel.addEventListener('submit', (event) => {
    event.preventDefault();
    const amount = input.valueAsNumber;
    if (!Number.isInteger(amount) || amount <= currentBid || amount > money) {
      status.textContent = `Enter a whole bid above $${currentBid} and up to $${money}`;
      return;
    }
    currentBid = amount;
    input.min = String(currentBid + 1);
    status.textContent = `Bid submitted: $${currentBid}`;
  });
  passButton.addEventListener('click', () => {
    input.disabled = true;
    bidButton.disabled = true;
    passButton.disabled = true;
    status.textContent = 'Out of auction';
  });

  return panel;
}

function createPlayerRow(player, index, gameState) {
  const playerAlias = gameState.player_aliases?.[player] ?? player;
  const row = htmlElement('article', {
    className: 'player-row',
    'aria-label': `Player ${playerAlias}`,
  });
  row.style.setProperty('--player-color', PLAYER_COLORS[index % PLAYER_COLORS.length]);

  const plants = gameState.player_power_plants[player] || [];
  const info = htmlElement('div', { className: 'player-info' });
  const heading = htmlElement('div', { className: 'player-info-heading' });
  heading.append(
    htmlElement('span', { className: 'player-name', textContent: playerAlias }),
    htmlElement('span', { className: 'player-money', textContent: `$${gameState.player_money[player] ?? 0}` }),
  );
  const network = htmlElement('div', { className: 'player-network' });
  network.append(
    htmlElement('span', { className: 'network-count', textContent: countNetworkHouses(gameState.map_houses, player) }),
    htmlElement('span', { className: 'network-label', textContent: 'in network' }),
  );
  const money = gameState.player_money[player] ?? 0;
  info.append(
    heading,
    network,
    createResourceList(gameState.player_resources[player] || {}),
    createBidPanel(playerAlias, money),
  );
  row.appendChild(info);

  for (let slot = 0; slot < 3; slot += 1) {
    row.appendChild(createPlantSlot(playerAlias, plants[slot], slot));
  }
  return row;
}

export function updatePlayerBoard(gameState) {
  const players = gameState.player_turn_order.slice(0, 6);
  const rows = players.map((player, index) => createPlayerRow(player, index, gameState));
  document.getElementById('player-board').replaceChildren(...rows);
}

export const initPlayerBoard = updatePlayerBoard;