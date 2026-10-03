const PLAYER_COLORS = ['#e85d5d', '#519cde', '#43a047', '#fb8c00', '#9445aa', '#fdd835'];

export function playerLabel(gameState, player) {
  return gameState.player_aliases?.[player] || player;
}

export function currentPlayerOf(gameState) {
  return gameState.current_player || gameState.player_turn_order[0];
}

export function playerColor(gameState, player) {
  const index = gameState.player_turn_order.indexOf(player);
  return PLAYER_COLORS[Math.max(index, 0) % PLAYER_COLORS.length];
}
