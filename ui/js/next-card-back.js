import { htmlElement } from './dom-utils.js';

export function renderNextCardBack(nextCardBack) {
  const card = htmlElement('div', { className: nextCardBack.classes });

  card.append(
    htmlElement('span', { className: 'next-card-back-heading', textContent: nextCardBack.heading }),
    htmlElement('span', { className: 'next-card-back-label', textContent: nextCardBack.label }),
  );

  document.getElementById('next-card-back').replaceChildren(card);
}
