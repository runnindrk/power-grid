import { requestBuyHouses, requestHousePrice } from './game-api.js';
import { HOUSE_SELECT_PROMPT, setHousePurchaseStatus, updatePlayerBoard } from './player-board.js';
import { currentPlayerOf, playerLabel } from './players.js';

// Tracks the current player's pending house selection, quoting and buying it through the API.
export function initHousePurchase(gameState, map) {
  const currentPlayer = currentPlayerOf(gameState);
  const placementStatus = document.getElementById('placement-status');
  const pendingHouses = [];
  let isBuying = false;
  let quoteRequestId = 0;
  let quotedPrice = null;

  const setStatus = (message, disabled) => setHousePurchaseStatus(currentPlayer, message, disabled);
  const placements = () => pendingHouses.map(({ city, spot }) => ({ city, spot }));

  function clearSelection(message = HOUSE_SELECT_PROMPT) {
    pendingHouses.forEach(({ city, spot }) => map.setSpotSelected(city, spot, false));
    pendingHouses.length = 0;
    quoteRequestId += 1;
    quotedPrice = null;
    setStatus(message, true);
  }

  async function updateQuote() {
    const requestId = ++quoteRequestId;
    quotedPrice = null;
    if (pendingHouses.length === 0) {
      setStatus(HOUSE_SELECT_PROMPT, true);
      return;
    }

    setStatus('Calculating...', true);
    try {
      const result = await requestHousePrice(currentPlayer, placements());
      if (requestId !== quoteRequestId) return;
      quotedPrice = result.price;
      setStatus(`Total $${result.price}`, false);
    } catch (error) {
      if (requestId === quoteRequestId) setStatus(error.message, true);
    }
  }

  async function buyPendingHouses() {
    isBuying = true;
    setStatus('Buying houses...', true);
    try {
      const result = await requestBuyHouses(currentPlayer, placements());
      pendingHouses.forEach(({ city, spot }) => {
        gameState.map_houses[city][spot] = currentPlayer;
        map.setSpotOwner(city, spot, currentPlayer);
      });
      gameState.player_money[currentPlayer] -= result.price;
      updatePlayerBoard(gameState);
      const houseCount = pendingHouses.length;
      clearSelection(`Bought ${houseCount} ${houseCount === 1 ? 'house' : 'houses'} for $${result.price}`);
      placementStatus.textContent = `Houses placed for ${playerLabel(gameState, currentPlayer)}`;
    } catch (error) {
      setStatus(error.message, quotedPrice === null);
    } finally {
      isBuying = false;
    }
  }

  document.getElementById('player-board').addEventListener('click', (event) => {
    const buyButton = event.target.closest('.player-buy-houses-button');
    if (!buyButton || isBuying || pendingHouses.length === 0 || quotedPrice === null) return;
    if (buyButton.closest('.player-house-purchase-controls').dataset.playerId !== currentPlayer) return;
    buyPendingHouses();
  });

  map.onSpotToggle((city, spot) => {
    if (isBuying || gameState.map_houses[city][spot]) return;
    const index = pendingHouses.findIndex((house) => house.city === city && house.spot === spot);
    if (index >= 0) pendingHouses.splice(index, 1);
    else pendingHouses.push({ city, spot });
    map.setSpotSelected(city, spot, index < 0);
    updateQuote();
  });
}
