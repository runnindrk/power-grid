import { postApi } from './api-client.js';

export const requestHousePrice = (player, houses) => postApi('/api/house-price', { player, houses }, 'House price');

export const requestBuyHouses = (player, houses) => postApi('/api/buy-houses', { player, houses }, 'Buy houses');

export const requestResourcePrice = (player, resources) => (
  postApi('/api/resource-price', { player, resources }, 'Resource price')
);

export const requestBuyResources = (player, resources) => (
  postApi('/api/buy-resources', { player, resources }, 'Buy resources')
);

export const requestPlantResourceMove = (move) => postApi('/api/transfer-plant-resource', move, 'Move resource');

export const requestBureaucracy = (state) => postApi('/api/bureaucracy', state, 'Power');
