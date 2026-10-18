export function renderHeader(header) {
  const turnOrder = document.getElementById('turn-order');

  turnOrder.replaceChildren(document.createTextNode('Turn order: '));

  for (let index = 0; index < header.turn_order.length; index += 1) {
    const player = header.turn_order[index];

    if (index > 0) {
      turnOrder.appendChild(document.createTextNode(' → '));
    }

    const playerTurn = document.createElement('span');

    playerTurn.className = player.classes.join(' ');
    playerTurn.textContent = player.label;

    playerTurn.style.setProperty('--player-color', player.color);

    if (player.current) {
      playerTurn.setAttribute('aria-current', 'true');
    }

    turnOrder.appendChild(playerTurn);
  }

  document.getElementById('placement-status').textContent = header.placement_status;
}
