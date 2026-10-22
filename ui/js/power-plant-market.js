import { htmlElement } from './dom-utils.js';
import { postDiscardPowerPlant, postReadyToPower, postSelectPowerPlant } from './api.js';

function createFuelDisplay(fuel) {
  const container = htmlElement('div', { className: 'plant-fuels' });

  if (fuel.empty_label) {
    container.appendChild(htmlElement('span', {
      className: 'plant-no-fuel',
      textContent: fuel.empty_label,
    }));
    return container;
  }

  const options = htmlElement('div', { className: fuel.classes });

  for (const item of fuel.items) {
    if (item.join) {
      options.appendChild(htmlElement('span', { className: 'fuel-join', textContent: item.join }));
    }

    const element = htmlElement('span', {
      className: item.classes,
      title: item.label,
      'aria-label': item.aria_label,
    });

    element.append(
      htmlElement('span', { className: 'fuel-icon', textContent: item.icon }),
      htmlElement('span', { className: 'fuel-amount', textContent: item.amount }),
    );
    options.appendChild(element);
  }

  container.appendChild(options);

  return container;
}

// Storage metadata identifies the plant and slots involved in a drag-and-drop move.
function createPlantStorage(storage) {
  const element = htmlElement('div', {
    className: 'plant-storage',
    'aria-label': storage.aria_label,
  });

  for (const slot of storage.slots) {
    const slotElement = htmlElement('span', {
      className: slot.classes,
      draggable: slot.draggable,
      title: slot.title,
      'aria-label': slot.title,
    });

    slotElement.dataset.drag = JSON.stringify(slot.drag);
    slotElement.dataset.drop = JSON.stringify(slot.drop);
    element.appendChild(slotElement);
  }

  return element;
}

function createReadyToPowerButton(ready, refresh) {
  const button = htmlElement('button', {
    className: 'plant-ready-button',
    type: 'button',
    title: 'Ready to power',
    'aria-label': 'Ready to power',
    textContent: '⚡',
    'aria-pressed': ready.pressed,
  });

  button.addEventListener('click', () => {
    postReadyToPower(ready.player_id, ready.plant_id).then(refresh);
  });

  return button;
}

// Market selection and replacement share one accessible card interaction.
function makePlantCardInteractive(article, card, refresh) {
  if (!card.selectable && !card.discardable) {
    return;
  }

  const discarding = card.discardable;
  const activate = discarding
    ? () => postDiscardPowerPlant(card.discard_player, card.plant_id).then(refresh)
    : () => postSelectPowerPlant(card.plant_id).then(refresh);

  article.setAttribute('role', 'button');
  article.setAttribute('tabindex', '0');
  article.setAttribute('aria-pressed', discarding ? 'false' : card.selected);

  if (discarding) {
    article.setAttribute('aria-label', 'Discard power plant ' + card.plant_id);
  }

  article.addEventListener('click', (event) => {
    if (!event.target.closest('button, .plant-storage-slot')) {
      activate();
    }
  });
  article.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      activate();
    }
  });
}

export function createPlantCard(card, refresh) {
  const article = htmlElement('article', {
    className: card.classes,
    'data-plant-id': card.plant_id,
    'aria-label': card.aria_label,
  });

  makePlantCardInteractive(article, card, refresh);

  const heading = htmlElement('div', { className: 'plant-heading' });

  heading.append(
    htmlElement('span', { className: 'plant-number', textContent: card.plant_id }),
    htmlElement('span', { className: 'plant-kind', textContent: card.kind }),
  );
  article.appendChild(heading);

  if (card.unavailable) {
    article.appendChild(htmlElement('p', {
      className: 'plant-unavailable',
      textContent: 'Details unavailable',
    }));
    return article;
  }

  const output = htmlElement('div', { className: 'plant-output' });

  output.append(
    htmlElement('span', { className: 'output-icon', 'aria-hidden': 'true', textContent: '⌂' }),
    htmlElement('span', { className: 'output-count', textContent: card.houses }),
    htmlElement('span', { className: 'output-label', textContent: 'cities' }),
  );

  if (card.ready_to_power && !card.discardable) {
    output.appendChild(createReadyToPowerButton(card.ready_to_power, refresh));
  }
  article.appendChild(output);

  if (card.storage) {
    const fuelStorage = htmlElement('div', { className: 'plant-fuel-storage' });

    fuelStorage.append(createFuelDisplay(card.fuel), createPlantStorage(card.storage));
    article.appendChild(fuelStorage);
  } else {
    article.appendChild(createFuelDisplay(card.fuel));
  }

  return article;
}

export function renderPowerPlantMarket(cards, refresh) {
  const grid = document.querySelector('#power-plant-market .power-plant-grid');

  grid.replaceChildren();

  for (const card of cards) {
    grid.appendChild(createPlantCard(card, refresh));
  }
}
