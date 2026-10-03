export async function requestResourcePrice(player, resources) {
  const response = await fetch('/api/resource-price', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ player, resources }),
  });
  const result = await response.json();
  if (!response.ok) {
    throw new Error(result.error || 'Resource price request failed');
  }
  return result;
}

export async function requestBuyResources(player, resources) {
  const response = await fetch('/api/buy-resources', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ player, resources }),
  });
  const result = await response.json();
  if (!response.ok) {
    throw new Error(result.error || 'Resource purchase failed');
  }
  return result;
}