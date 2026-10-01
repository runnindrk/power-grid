import { initMap } from './map-view.js';
import { initMoneyCard } from './money-card.js';
import { initReplenishmentCard } from './replenishment-card.js';
import { fetchGameState } from './game-state.js';

async function initCards(gameState) {
  const cardsPanel = document.getElementById('cards-panel');
  await initMoneyCard(cardsPanel);
  await initReplenishmentCard(cardsPanel, gameState);
}

async function init() {
  const gameState = await fetchGameState();
  await Promise.all([initMap(gameState), initCards(gameState)]);
}

init().catch((error) => {
  console.error(error);
  document.getElementById('placement-status').textContent = 'Unable to load game data';
});
