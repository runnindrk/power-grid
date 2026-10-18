import { postPlantResourceMove } from './api.js';

// Returns the storage slot the event happened on, or null (e.g. when the player drags selected text).
function findStorageSlot(target) {
  if (target instanceof Element) {
    return target.closest('.plant-storage-slot');
  }

  return null;
}

// Lets the player drag a stored resource onto another storage slot; the backend decides if the move is valid.
export function initPlantResourceDragAndDrop(board, refresh) {
  board.addEventListener('dragstart', (event) => {
    const slot = findStorageSlot(event.target);

    if (slot === null) return;

    slot.classList.add('dragging');
    event.dataTransfer.effectAllowed = 'move';
    event.dataTransfer.setData('text/plain', slot.dataset.drag);
  });

  board.addEventListener('dragend', (event) => {
    const slot = findStorageSlot(event.target);

    if (slot !== null) {
      slot.classList.remove('dragging');
    }

    for (const dropTarget of board.querySelectorAll('.drop-target')) {
      dropTarget.classList.remove('drop-target');
    }
  });

  board.addEventListener('dragover', (event) => {
    const slot = findStorageSlot(event.target);

    if (slot === null) return;

    event.preventDefault();
    slot.classList.add('drop-target');
    event.dataTransfer.dropEffect = 'move';
  });

  board.addEventListener('dragleave', (event) => {
    const slot = findStorageSlot(event.target);

    if (slot === null) return;

    slot.classList.remove('drop-target');
  });

  board.addEventListener('drop', (event) => {
    const slot = findStorageSlot(event.target);

    if (slot === null) return;

    event.preventDefault();
    slot.classList.remove('drop-target');

    const source = JSON.parse(event.dataTransfer.getData('text/plain'));
    const target = JSON.parse(slot.dataset.drop);

    postPlantResourceMove(source, target).then(refresh);
  });
}
