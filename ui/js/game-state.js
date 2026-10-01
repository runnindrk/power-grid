import { fetchJson } from './data-source.js';

const GAME_STATE_URL = '../../game_info/game_state/power_grid_game_state.json';

export const fetchGameState = () => fetchJson(GAME_STATE_URL, { cache: 'no-store' });
