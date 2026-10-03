export async function requestBureaucracy(state) {
  const response = await fetch('/api/bureaucracy', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(state),
  });
  const result = await response.json();
  if (!response.ok) {
    throw new Error(result.error || 'Bureaucracy request failed');
  }
  return result;
}