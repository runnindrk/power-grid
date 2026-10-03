import { postApi } from './api-client.js';

export async function requestBureaucracy(state) {
  return postApi('/api/bureaucracy', state, 'Power');
}