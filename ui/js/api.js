function showStatus(status, message) {
  const element = document.getElementById('api-status');

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
    showStatus('error', 'Request failed');

    return { status: 'error', message: 'Request failed' };
  }
}

export function postHouseSpot(city, spot) {
  return postApi('/api/house-spot', { city: city, spot: spot });
}

export function postBuyHouses() {
  return postApi('/api/buy-houses', {});
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

export function postBid(player, amount) {
  return postApi('/api/bid', { player: player, amount: amount });
}

export function postPassBid(player) {
  return postApi('/api/bid/pass', { player: player });
}

export function postBureaucracy() {
  return postApi('/api/bureaucracy', {});
}
