import { fetchReplenishmentData } from './data-source.js';
import { htmlElement } from './dom-utils.js';
import { RESOURCE_ICONS } from './resource-icons.js';

const REPLENISHED_RESOURCES = ['coal', 'oil', 'trash', 'uranium'];

function renderReplenishmentCard(replenishmentData, { number_of_players: numPlayers, step: currentStep }) {
  const rates = replenishmentData[`${numPlayers}_players`] ?? Object.values(replenishmentData)[0];
  const stepKeys = Object.keys(rates);
  const isCurrent = (stepKey) => parseInt(stepKey, 10) === currentStep;

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
    const slot = htmlElement('div', { className: 'step-slot' });
    slot.appendChild(htmlElement('span', {
      className: `step-badge${isCurrent(stepKey) ? ' current' : ''}`,
      textContent: parseInt(stepKey, 10),
    }));
    stepBadges.appendChild(slot);
  });
  header.appendChild(stepBadges);
  card.appendChild(header);

  const grid = htmlElement('div', { className: 'replenishment-grid' });
  REPLENISHED_RESOURCES.forEach((resource, i) => {
    const row = htmlElement('div', { className: `replenishment-row ${i % 2 === 0 ? 'dark' : 'light'}` });
    row.appendChild(htmlElement('div', { className: 'resource-icon', textContent: RESOURCE_ICONS[resource] }));
    stepKeys.forEach((stepKey) => {
      row.appendChild(htmlElement('div', {
        className: `cell${isCurrent(stepKey) ? ' current' : ''}`,
        textContent: rates[stepKey][0][resource],
      }));
    });
    grid.appendChild(row);
  });
  card.appendChild(grid);
  return card;
}

export async function initReplenishmentCard(container, gameState) {
  container.appendChild(renderReplenishmentCard(await fetchReplenishmentData(), gameState));
}
