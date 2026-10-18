import { htmlElement } from './dom-utils.js';
import { postBid, postPassBid } from './api.js';

export function createBidPanel(player, refresh) {
  const bid = player.bid;
  const panel = htmlElement('form', { className: 'player-bid-panel', 'aria-label': bid.aria_label });

  const input = htmlElement('input', {
    className: 'bid-amount',
    type: 'number',
    min: bid.min,
    max: bid.max,
    step: '1',
    value: bid.value,
    required: 'required',
    'aria-label': bid.input_aria_label,
  });
  const field = htmlElement('label', { className: 'bid-field' });
  field.append(htmlElement('span', { textContent: 'Bid $' }), input);

  const bidButton = htmlElement('button', { className: 'bid-submit', type: 'submit', textContent: 'Bid' });
  const passButton = htmlElement('button', { className: 'bid-pass', type: 'button', textContent: 'Out' });
  const status = htmlElement('span', { className: 'bid-status', 'aria-live': 'polite', textContent: bid.status });

  input.disabled = bid.disabled;
  bidButton.disabled = bid.disabled;
  passButton.disabled = bid.disabled;
  panel.append(field, bidButton, passButton, status);

  panel.addEventListener('submit', (event) => {
    event.preventDefault();

    postBid(player.player, input.value).then(refresh);
  });

  passButton.addEventListener('click', () => {
    postPassBid(player.player).then(refresh);
  });

  return panel;
}
