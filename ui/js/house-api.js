import { postApi } from './api-client.js';

export async function requestHousePrice(player, houses) {
  return postApi('/api/house-price', { player, houses }, 'House price');
}

export async function requestBuyHouses(player, houses) {
  return postApi('/api/buy-houses', { player, houses }, 'Buy houses');
}
