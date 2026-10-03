import { currentPlayerOf, playerColor, playerLabel } from './players.js';

export function initGameHeader(gameState) {
  const currentPlayer = currentPlayerOf(gameState);
  const currentAction = String(gameState.current_action || 'building_houses').replaceAll('_', ' ');

  const turnOrder = document.getElementById('turn-order');
  turnOrder.replaceChildren(document.createTextNode('Turn order: '));
  gameState.player_turn_order.forEach((player, index) => {
    if (index > 0) turnOrder.appendChild(document.createTextNode(' → '));
    const isCurrent = player === currentPlayer;
    const playerTurn = document.createElement('span');
    playerTurn.className = `turn-order-player${isCurrent ? ' current' : ''}`;
    playerTurn.textContent = playerLabel(gameState, player);
    playerTurn.style.color = playerColor(gameState, player);
    if (isCurrent) playerTurn.setAttribute('aria-current', 'true');
    turnOrder.appendChild(playerTurn);
  });

  document.getElementById('placement-status').textContent =
    `${currentAction} · ${playerLabel(gameState, currentPlayer)}`;
}
