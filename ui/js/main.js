import { fetchGameState } from './data-source.js';
import { initGameHeader } from './game-header.js';
import { initHousePurchase } from './house-purchase.js';
import { initMap } from './map-view.js';
import { initMoneyCard } from './money-card.js';
import { initPlayerBoard } from './player-board.js';
import { initPowerPlantMarket } from './power-plant-market.js';
import { initReplenishmentCard } from './replenishment-card.js';
import { initResourceMarket } from './resource-market.js';

async function initCards(gameState) {
  const infoCards = document.getElementById('info-cards');
  await initMoneyCard(infoCards);
  await initReplenishmentCard(infoCards, gameState);
}

async function init() {
  const gameState = await fetchGameState();
  const [map, , plantsById] = await Promise.all([
    initMap(gameState),
    initCards(gameState),
    initPowerPlantMarket(gameState),
  ]);
  initGameHeader(gameState);
  initPlayerBoard(gameState, plantsById);
  initHousePurchase(gameState, map);
  initResourceMarket(gameState);
}

init().catch((error) => {
  console.error(error);
  document.getElementById('placement-status').textContent = 'Unable to load game data';
});
