function updateApiStatus(label, state, detail = '') {
  const status = document.getElementById('api-status');
  if (!status) return;
  status.dataset.state = state;
  status.textContent = detail ? `${label}: ${detail}` : label;
  status.title = status.textContent;
}

export async function postApi(url, payload, label) {
  updateApiStatus(label, 'pending', 'pending');

  let response;
  try {
    response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
  } catch (error) {
    updateApiStatus(label, 'error', 'network error');
    throw error;
  }

  let result = {};
  try {
    result = await response.json();
  } catch (error) {
    updateApiStatus(label, 'error', `HTTP ${response.status}: invalid response`);
    throw new Error(`${label} returned an invalid response`);
  }

  const succeeded = response.ok && (result.error_code === undefined || result.error_code === 0);
  const errorCode = result.error_code;
  const errorName = errorCode === 0
    ? 'E_OK'
    : errorCode === 1
      ? 'E_NOT_OKAY'
      : `E_${errorCode}`;
  const statusText = errorCode === undefined
    ? `HTTP ${response.status}`
    : `${errorName} · HTTP ${response.status}`;
  updateApiStatus(label, succeeded ? 'ok' : 'error', statusText);

  if (!succeeded) {
    throw new Error(result.error || `${label} failed (${statusText})`);
  }
  return result;
}