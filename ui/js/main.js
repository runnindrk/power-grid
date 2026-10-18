import { fetchView } from './api.js';
import { renderHeader } from './game-header.js';
import { renderMap } from './map-view.js';
import { initMapPanZoom } from './map-pan-zoom.js';
import { renderMoneyCard } from './money-card.js';
import { renderNextCardBack } from './next-card-back.js';
import { initPlantResourceDragAndDrop } from './plant-resource-dnd.js';
import { renderPlayerBoard } from './player-board.js';
import { renderPowerPlantMarket } from './power-plant-market.js';
import { renderReplenishmentCard } from './replenishment-card.js';
import { renderResourceMarket } from './resource-market.js';

// Draws the whole page from the view sent by the backend.
function render(view) {
  renderMap(view.map, refresh);
  renderHeader(view.header);
  renderPlayerBoard(view.players, refresh);
  renderPowerPlantMarket(view.power_plant_market, refresh);
  renderResourceMarket(view.resource_market);
  renderNextCardBack(view.next_card_back);

  document.getElementById('info-cards').replaceChildren(
    renderMoneyCard(view.money),
    renderReplenishmentCard(view.replenishment),
  );
}

// Asks the backend for the current view and draws it; called after every action.
async function refresh() {
  render(await fetchView());
}

async function init() {
  initPlantResourceDragAndDrop(document.getElementById('player-board'), refresh);

  await refresh();

  initMapPanZoom(document.getElementById('map'));
}

init().catch((error) => {
  console.error(error);

  document.getElementById('placement-status').textContent = 'Unable to load game data';
});
