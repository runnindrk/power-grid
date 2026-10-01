import { fetchJson } from './data-source.js';
import { htmlElement } from './dom-utils.js';

const REPLENISHMENT_DATA_URL = '../../game_info/static_info/power_grid_replenishment.json';

const resourceIcons = {
  coal: '🪨', oil: '🛢️', trash: '🗑️', uranium: '☢️',
};

function renderReplenishmentCard(replenishmentData, gameState) {
  const numPlayers = gameState ? gameState.number_of_players : null;
  const currentStep = gameState ? gameState.step : null;
  const playerKey = numPlayers ? `${numPlayers}_players` : Object.keys(replenishmentData)[0];
  const players = replenishmentData[playerKey] || replenishmentData[Object.keys(replenishmentData)[0]];
  const stepKeys = Object.keys(players);

  const card = htmlElement('div', { className: 'info-card replenishment-card' });
  const header = htmlElement('div', { className: 'replenishment-header' });
  const playerSlot = htmlElement('div', { className: 'player-slot' });
  playerSlot.appendChild(htmlElement('span', {
    className: 'player-badge',
    title: 'Number of players',
    textContent: numPlayers ?? '-',
  }));
  header.appendChild(playerSlot);

  const stepBadges = htmlElement('div', { className: 'step-badges' });
  stepKeys.forEach((stepKey) => {
    const stepNum = parseInt(stepKey, 10);
    const slot = htmlElement('div', { className: 'step-slot' });
    const badge = htmlElement('span', { className: 'step-badge', textContent: stepNum });
    if (stepNum === currentStep) badge.classList.add('current');
    slot.appendChild(badge);
    stepBadges.appendChild(slot);
  });
  header.appendChild(stepBadges);
  card.appendChild(header);

  const grid = htmlElement('div', { className: 'replenishment-grid' });
  Object.keys(resourceIcons).forEach((resource, i) => {
    const row = htmlElement('div', { className: `replenishment-row ${i % 2 === 0 ? 'dark' : 'light'}` });
    const icon = htmlElement('div', { className: 'resource-icon', textContent: resourceIcons[resource] });
    row.appendChild(icon);
    stepKeys.forEach((stepKey) => {
      const cell = htmlElement('div', { className: 'cell', textContent: players[stepKey][0][resource] });
      if (parseInt(stepKey, 10) === currentStep) cell.classList.add('current');
      row.appendChild(cell);
    });
    grid.appendChild(row);
  });
  card.appendChild(grid);
  return card;
}

export async function initReplenishmentCard(container, gameState) {
  const replenishmentData = await fetchJson(REPLENISHMENT_DATA_URL);
  container.appendChild(renderReplenishmentCard(replenishmentData, gameState));
}
