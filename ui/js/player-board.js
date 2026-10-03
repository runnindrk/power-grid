import { htmlElement } from './dom-utils.js';
import { requestBureaucracy } from './bureaucracy-api.js';
import { createPlantCard } from './power-plant-market.js';
import { requestBuyResources, requestResourcePrice } from './resources-api.js';

const PLAYER_COLORS = ['#e85d5d', '#519cde', '#43a047', '#fb8c00', '#9445aa', '#fdd835'];
const RESOURCE_DETAILS = [
  ['coal', 'Coal'],
  ['oil', 'Oil'],
  ['trash', 'Trash'],
  ['uranium', 'Nuclear'],
];

function countNetworkHouses(mapHouses, player) {
  return Object.values(mapHouses).reduce((count, citySpots) => (
    count + Object.values(citySpots).filter((owner) => owner === player).length
  ), 0);
}

function createPlantSlot(playerAlias, ownedPlant, slotIndex, plantsById) {
  if (ownedPlant) {
    const plantId = ownedPlant.plant_id;
    return createPlantCard(plantId, plantsById.get(plantId), true, ownedPlant.resources);
  }

  const slot = htmlElement('div', {
    className: 'player-plant-slot empty',
    'aria-label': `Empty power plant slot ${slotIndex + 1} for ${playerAlias}`,
  });
  slot.appendChild(htmlElement('span', {
    className: 'empty-slot-label',
    textContent: 'Empty',
  }));
  return slot;
}

function createResourceBuyPanel(player, playerAlias) {
  const panel = htmlElement('form', {
    className: 'player-resource-buy-panel',
    'aria-label': `Buy resources for ${playerAlias}`,
  });
  const quantities = [];
  const options = htmlElement('div', { className: 'resource-buy-options' });
  RESOURCE_DETAILS.forEach(([resource, label]) => {
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

  const buyButton = htmlElement('button', {
    className: 'resource-buy-button',
    type: 'submit',
    'aria-label': `Buy selected resources for ${playerAlias}`,
  });
  const buyPrice = htmlElement('span', {
    className: 'resource-buy-total',
    textContent: '$0',
  });
  buyButton.append(
    htmlElement('span', { className: 'resource-buy-label', textContent: 'Buy' }),
    buyPrice,
  );
  panel.append(options, buyButton);

  let quoteRequestId = 0;

  function getResources() {
    return Object.fromEntries(quantities.map(({ resource, input }) => [
      resource,
      input.value === '' ? 0 : input.valueAsNumber,
    ]));
  }

  async function updateQuote() {
    const requestId = ++quoteRequestId;
    try {
      const result = await requestResourcePrice(player, getResources());
      if (requestId !== quoteRequestId) return;
      if (result.error_code === 0) buyPrice.textContent = `$${result.price}`;
    } catch (error) {
      console.error(error);
    }
  }

  quantities.forEach(({ input }) => input.addEventListener('input', updateQuote));

  panel.addEventListener('submit', async (event) => {
    event.preventDefault();
    try {
      const result = await requestBuyResources(player, getResources());
      if (result.error_code === 0) buyPrice.textContent = `$${result.price}`;
    } catch (error) {
      console.error(error);
    }
  });
  return panel;
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
    textContent: 'Out',
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
    currentBid = amount;
    input.min = String(currentBid + 1);
    status.textContent = `Bid: $${currentBid}`;
  });
  passButton.addEventListener('click', () => {
    input.disabled = true;
    bidButton.disabled = true;
    passButton.disabled = true;
    status.textContent = 'Out';
  });

  return panel;
}

function createPowerButton(gameState) {
  const button = htmlElement('button', {
    className: 'player-power-button',
    type: 'button',
    textContent: 'Power',
  });
  button.addEventListener('click', async () => {
    try {
      await requestBureaucracy(gameState);
    } catch (error) {
      console.error(error);
    }
  });
  return button;
}

function createPlayerRow(player, index, gameState, plantsById) {
  const playerAlias = gameState.player_aliases?.[player] ?? player;
  const row = htmlElement('article', {
    className: 'player-row',
    'data-player-id': player,
    'aria-label': `Player ${playerAlias}`,
  });
  row.style.setProperty('--player-color', PLAYER_COLORS[index % PLAYER_COLORS.length]);

  const plants = gameState.player_power_plants[player] || [];
  const info = htmlElement('div', { className: 'player-info' });
  const heading = htmlElement('div', { className: 'player-info-heading' });
  const network = htmlElement('div', { className: 'player-network' });
  network.append(
    htmlElement('span', { className: 'network-count', textContent: countNetworkHouses(gameState.map_houses, player) }),
    htmlElement('span', { className: 'network-label', textContent: 'in network' }),
  );
  const money = gameState.player_money[player] ?? 0;
  heading.append(
    htmlElement('span', { className: 'player-name', textContent: playerAlias }),
    network,
    htmlElement('span', { className: 'player-money', textContent: `$${money}` }),
  );
  const housePurchaseControls = htmlElement('div', {
    className: 'player-house-purchase-controls',
    'data-player-id': player,
  });
  housePurchaseControls.append(
    htmlElement('span', {
      className: 'player-house-purchase-total',
      'aria-live': 'polite',
      textContent: player === gameState.current_player ? 'Select house spots' : 'Waiting for turn',
    }),
    htmlElement('button', {
      className: 'player-buy-houses-button',
      type: 'button',
      textContent: 'Buy houses',
      'aria-label': `Buy houses for ${playerAlias}`,
      disabled: 'disabled',
    }),
  );
  const actions = htmlElement('div', { className: 'player-actions' });
  actions.append(
    createBidPanel(playerAlias, money),
    createResourceBuyPanel(player, playerAlias),
    housePurchaseControls,
    createPowerButton(gameState),
  );
  info.append(
    heading,
    actions,
  );
  row.appendChild(info);

  for (let slot = 0; slot < 3; slot += 1) {
    row.appendChild(createPlantSlot(playerAlias, plants[slot], slot, plantsById));
  }
  return row;
}

export function updatePlayerBoard(gameState, plantsById) {
  const players = gameState.player_turn_order.slice(0, 6);
  const rows = players.map((player, index) => createPlayerRow(player, index, gameState, plantsById));
  document.getElementById('player-board').replaceChildren(...rows);
}

export const initPlayerBoard = updatePlayerBoard;