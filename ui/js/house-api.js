export async function requestHousePlacement(player, city, spot) {
  const response = await fetch('/api/place-house', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ player, city, spot }),
  });
  const state = await response.json();
  if (!response.ok) {
    throw new Error(state.error || 'House placement was rejected');
  }
  return state;
}