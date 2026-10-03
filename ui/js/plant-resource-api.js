import { postApi } from './api-client.js';

export async function requestPlantResourceMove({
  player,
  source_plant_id,
  source_slot,
  target_plant_id,
  target_slot,
}) {
  return postApi('/api/transfer-plant-resource', {
    player,
    source_plant_id,
    source_slot,
    target_plant_id,
    target_slot,
  }, 'Move resource');
}