import { htmlElement } from './dom-utils.js';

export function renderReplenishmentCard(replenishment) {
  const playerSlot = htmlElement('div', { className: 'player-slot' });

  playerSlot.appendChild(htmlElement('span', {
    className: 'player-badge',
    title: 'Number of players',
    textContent: replenishment.player_count,
  }));

  const stepBadges = htmlElement('div', { className: 'step-badges' });

  for (const step of replenishment.steps) {
    const slot = htmlElement('div', { className: 'step-slot' });

    slot.appendChild(htmlElement('span', { className: step.classes, textContent: step.label }));
    stepBadges.appendChild(slot);
  }

  const header = htmlElement('div', { className: 'replenishment-header' });

  header.append(playerSlot, stepBadges);

  const grid = htmlElement('div', { className: 'replenishment-grid' });

  for (const row of replenishment.rows) {
    const element = htmlElement('div', { className: row.classes });

    element.appendChild(htmlElement('div', { className: 'resource-icon', textContent: row.icon }));

    for (const cell of row.cells) {
      element.appendChild(htmlElement('div', { className: cell.classes, textContent: cell.value }));
    }

    grid.appendChild(element);
  }

  const card = htmlElement('div', { className: 'info-card replenishment-card' });

  card.append(header, grid);

  return card;
}
