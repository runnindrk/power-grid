import { htmlElement } from './dom-utils.js';
import { createBidPanel } from './bid-panel.js';
import { requestBureaucracy } from './game-api.js';
import { initPlantResourceDragAndDrop } from './plant-resource-dnd.js';
import { createPlantCard } from './power-plant-market.js';
import { currentPlayerOf, playerColor, playerLabel } from './players.js';
import { createResourceBuyPanel } from './resource-buy-panel.js';

const MAX_PLAYERS = 6;
const PLANT_SLOTS_PER_PLAYER = 3;

export const HOUSE_SELECT_PROMPT = 'Select house spots';

let plantsById;

function countNetworkHouses(mapHouses, player) {
  return Object.values(mapHouses).reduce((count, citySpots) => (
    count + Object.values(citySpots).filter((owner) => owner === player).length
  ), 0);
}

function createPlantSlot(player, playerAlias, ownedPlant, slotIndex) {
  if (ownedPlant) {
    const { plant_id: plantId, resources } = ownedPlant;
    return createPlantCard(plantId, plantsById.get(plantId), { playerId: player, resources });
  }

  const slot = htmlElement('div', {
    className: 'player-plant-slot empty',
    'aria-label': `Empty power plant slot ${slotIndex + 1} for ${playerAlias}`,
  });
  slot.appendChild(htmlElement('span', { className: 'empty-slot-label', textContent: 'Empty' }));
  return slot;
}

function createHousePurchaseControls(player, playerAlias, isCurrentPlayer) {
  const controls = htmlElement('div', {
    className: 'player-house-purchase-controls',
    'data-player-id': player,
  });
  controls.append(
    htmlElement('span', {
      className: 'player-house-purchase-total',
      'aria-live': 'polite',
      textContent: isCurrentPlayer ? HOUSE_SELECT_PROMPT : 'Waiting for turn',
    }),
    htmlElement('button', {
      className: 'player-buy-houses-button',
      type: 'button',
      textContent: 'Buy houses',
      'aria-label': `Buy houses for ${playerAlias}`,
      disabled: 'disabled',
    }),
  );
  return controls;
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

function createPlayerInfo(gameState, player, playerAlias) {
  const money = gameState.player_money[player] ?? 0;
  const network = htmlElement('div', { className: 'player-network' });
  network.append(
    htmlElement('span', {
      className: 'network-count',
      textContent: countNetworkHouses(gameState.map_houses, player),
    }),
    htmlElement('span', { className: 'network-label', textContent: 'in network' }),
  );
  const heading = htmlElement('div', { className: 'player-info-heading' });
  heading.append(
    htmlElement('span', { className: 'player-name', textContent: playerAlias }),
    network,
    htmlElement('span', { className: 'player-money', textContent: `$${money}` }),
  );

  const actions = htmlElement('div', { className: 'player-actions' });
  actions.append(
    createBidPanel(playerAlias, money),
    createResourceBuyPanel(player, playerAlias),
    createHousePurchaseControls(player, playerAlias, player === currentPlayerOf(gameState)),
    createPowerButton(gameState),
  );

  const info = htmlElement('div', { className: 'player-info' });
  info.append(heading, actions);
  return info;
}

function createPlayerRow(gameState, player) {
  const playerAlias = playerLabel(gameState, player);
  const row = htmlElement('article', {
    className: 'player-row',
    'data-player-id': player,
    'aria-label': `Player ${playerAlias}`,
  });
  row.style.setProperty('--player-color', playerColor(gameState, player));

  const plants = gameState.player_power_plants[player] || [];
  row.appendChild(createPlayerInfo(gameState, player, playerAlias));
  for (let slot = 0; slot < PLANT_SLOTS_PER_PLAYER; slot += 1) {
    row.appendChild(createPlantSlot(player, playerAlias, plants[slot], slot));
  }
  return row;
}

export function setHousePurchaseStatus(player, message, disabled) {
  const row = document.querySelector(`#player-board .player-row[data-player-id="${player}"]`);
  if (!row) return;
  row.querySelector('.player-house-purchase-total').textContent = message;
  row.querySelector('.player-buy-houses-button').disabled = disabled;
}

export function updatePlayerBoard(gameState) {
  const rows = gameState.player_turn_order.slice(0, MAX_PLAYERS).map((player) => createPlayerRow(gameState, player));
  document.getElementById('player-board').replaceChildren(...rows);
}

export function initPlayerBoard(gameState, plants) {
  plantsById = plants;
  updatePlayerBoard(gameState);
  initPlantResourceDragAndDrop(document.getElementById('player-board'), (updatedState) => {
    // Only plants are taken from the server; houses are tracked client-side until persisted.
    gameState.player_power_plants = updatedState.player_power_plants;
    updatePlayerBoard(gameState);
  });
}
