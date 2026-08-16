import { initMap } from './map-view.js';
import { initMoneyCard } from './money-card.js';
import { initReplenishmentCard } from './replenishment-card.js';
import { fetchGameState } from './game-state.js';

async function initCards() {
  const gameState = await fetchGameState();
  const cardsPanel = document.getElementById('cards-panel');
  await initMoneyCard(cardsPanel);
  await initReplenishmentCard(cardsPanel, gameState);
}

initMap();
initCards();
