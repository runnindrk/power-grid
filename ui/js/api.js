function showStatus(status, message) {
  const element = document.getElementById('api-status');

  if (element === null) return;

  element.dataset.state = status;
  element.textContent = message;
  element.title = message;
}

export async function fetchView() {
  const response = await fetch('/api/view', { cache: 'no-store' });

  if (!response.ok) {
    throw new Error('Failed to load /api/view: ' + response.status);
  }

  return response.json();
}

export function postSaveGame() {
  return postApi('/api/save-game', {});
}

export function postNewGame(numberOfPlayers) {
  return postApi('/api/new-game', { number_of_players: numberOfPlayers });
}

export function postLoadGame(saveId) {
  return postApi('/api/load-game', { save_id: saveId });
}

export async function fetchSavedGames() {
  try {
    const response = await fetch('/api/game-saves', { cache: 'no-store' });

    if (!response.ok) return [];

    return (await response.json()).saves;
  } catch (error) {
    return [];
  }
}

async function postApi(url, payload) {
  showStatus('pending', 'Sending…');

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    const result = await response.json();

    showStatus(result.status, result.message);
    return result;
  } catch (error) {
    showStatus('error', 'Request Failed');

    return { status: 'error', message: 'Request Failed' };
  }
}

export function postHouseSpot(city, spot) {
  return postApi('/api/house-spot', { city: city, spot: spot });
}

export function postBuyHouses(player) {
  return postApi('/api/buy-houses', { player: player });
}

export function postResourcePrice(player, resources) {
  return postApi('/api/resource-price', { player: player, resources: resources });
}

export function postBuyResources(player, resources) {
  return postApi('/api/buy-resources', { player: player, resources: resources });
}

export function postPlantResourceMove(source, target) {
  return postApi('/api/transfer-plant-resource', {
    player: source.player,
    source_plant_id: source.source_plant_id,
    source_slot: source.source_slot,
    target_plant_id: target.target_plant_id,
    target_slot: target.target_slot,
  });
}

export function postReadyToPower(player, plantId) {
  return postApi('/api/plant/ready-to-power', { player: player, plant_id: plantId });
}

export function postSelectPowerPlant(plantId) {
  return postApi('/api/plant/select', { plant_id: plantId });
}

export function postDiscardPowerPlant(player, plantId) {
  return postApi('/api/plant/discard', { player: player, plant_id: plantId });
}

export function postBid(player, amount) {
  return postApi('/api/bid', { player: player, amount: amount });
}

export function postPassBid(player) {
  return postApi('/api/bid/pass', { player: player });
}

export function postBureaucracy(player) {
  return postApi('/api/bureaucracy', { player: player });
}
