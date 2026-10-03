import { htmlElement } from './dom-utils.js';

export function createBidPanel(playerAlias, money) {
  const panel = htmlElement('form', {
    className: 'player-bid-panel',
    'aria-label': `Power plant bid for ${playerAlias}`,
  });
  const input = htmlElement('input', {
    className: 'bid-amount',
    type: 'number',
    min: '1',
    max: String(money),
    step: '1',
    value: '1',
    required: 'required',
    'aria-label': `Bid amount for ${playerAlias}`,
  });
  const label = htmlElement('label', { className: 'bid-field' });
  label.append(htmlElement('span', { textContent: 'Bid $' }), input);

  const bidButton = htmlElement('button', { className: 'bid-submit', type: 'submit', textContent: 'Bid' });
  const passButton = htmlElement('button', { className: 'bid-pass', type: 'button', textContent: 'Out' });
  const status = htmlElement('span', {
    className: 'bid-status',
    'aria-live': 'polite',
    textContent: 'No bid yet',
  });
  panel.append(label, bidButton, passButton, status);

  panel.addEventListener('submit', (event) => {
    event.preventDefault();
    const amount = input.valueAsNumber;
    input.min = String(amount + 1);
    status.textContent = `Bid: $${amount}`;
  });
  passButton.addEventListener('click', () => {
    input.disabled = true;
    bidButton.disabled = true;
    passButton.disabled = true;
    status.textContent = 'Out';
  });

  return panel;
}
