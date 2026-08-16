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

  const card = document.createElement('div');
  card.className = 'info-card replenishment-card';

  const header = document.createElement('div');
  header.className = 'replenishment-header';
  header.innerHTML = `<div class="player-slot"><span class="player-badge" title="Number of players">${numPlayers ?? '-'}</span></div>`;
  const stepBadges = document.createElement('div');
  stepBadges.className = 'step-badges';
  stepKeys.forEach((stepKey) => {
    const stepNum = parseInt(stepKey, 10);
    const slot = document.createElement('div');
    slot.className = 'step-slot';
    const badge = document.createElement('span');
    badge.className = 'step-badge';
    badge.textContent = stepNum;
    if (stepNum === currentStep) badge.classList.add('current');
    slot.appendChild(badge);
    stepBadges.appendChild(slot);
  });
  header.appendChild(stepBadges);
  card.appendChild(header);

  const grid = document.createElement('div');
  grid.className = 'replenishment-grid';
  Object.keys(resourceIcons).forEach((resource, i) => {
    const row = document.createElement('div');
    row.className = `replenishment-row ${i % 2 === 0 ? 'dark' : 'light'}`;
    const icon = document.createElement('div');
    icon.className = 'resource-icon';
    icon.textContent = resourceIcons[resource];
    row.appendChild(icon);
    stepKeys.forEach((stepKey) => {
      const cell = document.createElement('div');
      cell.className = 'cell';
      cell.textContent = players[stepKey][0][resource];
      if (parseInt(stepKey, 10) === currentStep) cell.classList.add('current');
      row.appendChild(cell);
    });
    grid.appendChild(row);
  });
  card.appendChild(grid);
  return card;
}

export async function initReplenishmentCard(container, gameState) {
  const res = await fetch(REPLENISHMENT_DATA_URL);
  const replenishmentData = await res.json();
  container.appendChild(renderReplenishmentCard(replenishmentData, gameState));
}
