const GAME_INFO_URL = '/game_info';

export const OUTLINE_IMAGE_URL = `${GAME_INFO_URL}/maps/germany/germany_outline.jpg`;

async function fetchJson(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) {
    throw new Error(`Failed to load ${url}: ${response.status} ${response.statusText}`);
  }
  return response.json();
}

export const fetchGameState = () => (
  fetchJson(`${GAME_INFO_URL}/game_state/power_grid_game_state.json`, { cache: 'no-store' })
);
export const fetchMapData = () => fetchJson(`${GAME_INFO_URL}/maps/germany/power_grid_germany_map.json`);
export const fetchPlantDeck = () => fetchJson(`${GAME_INFO_URL}/static_info/power_grid_deck_set_0.json`);
export const fetchMoneyData = () => fetchJson(`${GAME_INFO_URL}/static_info/power_grid_money.json`);
export const fetchReplenishmentData = () => fetchJson(`${GAME_INFO_URL}/static_info/power_grid_replenishment.json`);
