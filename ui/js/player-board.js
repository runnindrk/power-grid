import { htmlElement } from './dom-utils.js';
import { postBureaucracy, postBuyHouses } from './api.js';
import { createBidPanel } from './bid-panel.js';
import { createPlantCard } from './power-plant-market.js';
import { createResourceBuyPanel } from './resource-buy-panel.js';

function createPlantSlot(slot, refresh) {
  if (!slot.empty) {
    return createPlantCard(slot, refresh);
  }

  const element = htmlElement('div', { className: slot.classes, 'aria-label': slot.aria_label });

  element.appendChild(htmlElement('span', { className: 'empty-slot-label', textContent: slot.label }));

  return element;
}

function createHousePurchaseButton(player, refresh) {
  const purchase = player.house_purchase;
  const button = htmlElement('button', {
    className: 'player-buy-houses-button',
    type: 'button',
    'aria-label': purchase.aria_label,
  });

  button.append(
    htmlElement('span', { className: 'house-button-label', textContent: purchase.label }),
    htmlElement('span', { className: 'house-button-total', 'aria-live': 'polite', textContent: purchase.total }),
  );
  button.disabled = purchase.buy_disabled;
  button.addEventListener('click', () => {
    postBuyHouses().then(refresh);
  });

  return button;
}

function createPowerButton(refresh) {
  const button = htmlElement('button', { className: 'player-power-button', type: 'button', textContent: 'Power' });

  button.addEventListener('click', () => {
    postBureaucracy().then(refresh);
  });

  return button;
}

function createPlayerInfo(player, refresh) {
  const network = htmlElement('div', { className: 'player-network' });

  network.append(
    htmlElement('span', { className: 'network-count', textContent: player.network.count }),
    htmlElement('span', { className: 'network-label', textContent: player.network.label }),
  );

  const heading = htmlElement('div', { className: 'player-info-heading' });
  const title = htmlElement('div', { className: 'player-title' });

  title.append(
    htmlElement('span', { className: 'player-name', textContent: player.label }),
    htmlElement('span', { className: 'player-separator', textContent: '·' }),
    network,
  );
  heading.append(
    title,
    htmlElement('span', { className: 'player-money', textContent: player.money.label }),
  );

  const actions = htmlElement('div', { className: 'player-actions' });
  const pair = htmlElement('div', { className: 'player-action-pair' });

  pair.append(
    createResourceBuyPanel(player, refresh),
    createHousePurchaseButton(player, refresh),
    createPowerButton(refresh),
  );
  actions.append(
    createBidPanel(player, refresh),
    pair,
  );

  const info = htmlElement('div', { className: 'player-info' });

  info.append(heading, actions);

  return info;
}

function createPlayerRow(player, refresh) {
  const row = htmlElement('article', {
    className: 'player-row',
    'data-player-id': player.player,
    'aria-label': player.aria_label,
  });

  row.style.setProperty('--player-color', player.color);
  row.appendChild(createPlayerInfo(player, refresh));

  for (const slot of player.plant_slots) {
    row.appendChild(createPlantSlot(slot, refresh));
  }

  return row;
}

export function renderPlayerBoard(players, refresh) {
  const board = document.getElementById('player-board');

  board.replaceChildren();

  for (const player of players) {
    board.appendChild(createPlayerRow(player, refresh));
  }
}
