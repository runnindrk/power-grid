export async function requestHousePrice(player, houses) {
  const response = await fetch('/api/house-price', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ player, houses }),
  });
  const result = await response.json();
  if (!response.ok) {
    throw new Error(result.error || 'House price request failed');
  }
  return result;
}

export async function requestBuyHouses(player, houses) {
  const response = await fetch('/api/buy-houses', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ player, houses }),
  });
  const result = await response.json();
  if (!response.ok) {
    throw new Error(result.error || 'House purchase failed');
  }
  return result;
}
