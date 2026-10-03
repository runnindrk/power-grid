import { postApi } from './api-client.js';

export async function requestResourcePrice(player, resources) {
  return postApi('/api/resource-price', { player, resources }, 'Resource price');
}

export async function requestBuyResources(player, resources) {
  return postApi('/api/buy-resources', { player, resources }, 'Buy resources');
}