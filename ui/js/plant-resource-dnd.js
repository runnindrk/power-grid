import { requestPlantResourceMove } from './game-api.js';

const STORAGE_SLOT_SELECTOR = '.plant-storage-slot';

function getStorageSlot(target) {
  return target instanceof Element ? target.closest(STORAGE_SLOT_SELECTOR) : null;
}

function getDragPayload(slot) {
  return {
    player: slot.dataset.playerId,
    source_plant_id: Number(slot.dataset.plantId),
    source_slot: Number(slot.dataset.slotIndex),
  };
}

export function initPlantResourceDragAndDrop(board, onGameStateUpdated) {
  let draggedResource = null;

  board.addEventListener('dragstart', (event) => {
    const slot = getStorageSlot(event.target);
    if (!slot?.classList.contains('filled')) {
      event.preventDefault();
      return;
    }

    draggedResource = getDragPayload(slot);
    slot.classList.add('dragging');
    if (event.dataTransfer) {
      event.dataTransfer.effectAllowed = 'move';
      event.dataTransfer.setData('text/plain', JSON.stringify(draggedResource));
    }
  });

  board.addEventListener('dragend', (event) => {
    getStorageSlot(event.target)?.classList.remove('dragging');
    draggedResource = null;
    board.querySelectorAll('.drop-target').forEach((slot) => slot.classList.remove('drop-target'));
  });

  board.addEventListener('dragover', (event) => {
    const slot = getStorageSlot(event.target);
    if (!slot) return;
    event.preventDefault();
    slot.classList.add('drop-target');
    if (event.dataTransfer) event.dataTransfer.dropEffect = 'move';
  });

  board.addEventListener('dragleave', (event) => {
    getStorageSlot(event.target)?.classList.remove('drop-target');
  });

  board.addEventListener('drop', async (event) => {
    const target = getStorageSlot(event.target);
    if (!target) return;
    event.preventDefault();
    target.classList.remove('drop-target');

    let source = draggedResource;
    if (event.dataTransfer) {
      try {
        source = JSON.parse(event.dataTransfer.getData('text/plain'));
      } catch (error) {
        console.error(error);
        return;
      }
    }
    if (!source) return;

    try {
      const result = await requestPlantResourceMove({
        ...source,
        target_plant_id: Number(target.dataset.plantId),
        target_slot: Number(target.dataset.slotIndex),
      });
      onGameStateUpdated(result.game_state);
    } catch (error) {
      console.error(error);
    }
  });
}