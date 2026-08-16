const GAME_STATE_URL = '../../game_info/game_state/power_grid_game_state.json';

export async function fetchGameState() {
  const res = await fetch(GAME_STATE_URL);
  return res.json();
}
