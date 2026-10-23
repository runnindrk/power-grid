export function renderHeader(header) {
  const turnOrder = document.getElementById('turn-order');
  document.getElementById('cycles').textContent = 'Cycles: ' + header.cycles;

  turnOrder.replaceChildren(document.createTextNode('Turn order: '));

  for (let index = 0; index < header.turn_order.length; index += 1) {
    const player = header.turn_order[index];

    if (index > 0) {
      const arrow = header.reverse_turn_direction ? ' ← ' : ' → ';

      turnOrder.appendChild(document.createTextNode(arrow));
    }

    const playerTurn = document.createElement('span');

    playerTurn.className = player.classes.join(' ');
    playerTurn.textContent = player.label;

    playerTurn.style.setProperty('--player-color', player.color);

    if (player.current) {
      playerTurn.setAttribute('aria-current', 'true');
    }

    if (player.passed) {
      playerTurn.title = 'Passed on this plant';
    }

    turnOrder.appendChild(playerTurn);
  }

  document.getElementById('placement-status').textContent = header.placement_status;
}
