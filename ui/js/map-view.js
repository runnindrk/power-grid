import { el } from './dom-utils.js';
import { OUTLINE_IMAGE_URL, fetchMapData } from './data-source.js';
import { createMapModel } from './map-model.js';
import { REGION_COLORS, costColor, housePath, pointAtAngle, wedgePath } from './map-shapes.js';
import { playerColor, playerLabel } from './players.js';

const HOUSE_SPOTS = ['spot_1', 'spot_2', 'spot_3'];
const EMPTY_SPOT_COLOR = '#30343b';
const SPOT_RADIUS = 11;
const MARK_RADIUS = 5.5;

function spotDescription(gameState, cityName, spot, owner) {
  return `${cityName}, ${spot.replace('_', ' ')}: ${owner ? playerLabel(gameState, owner) : 'empty'}`;
}

function applySpotOwner(gameState, spotGroup, cityName, spot, owner) {
  const description = spotDescription(gameState, cityName, spot, owner);
  spotGroup.classList.toggle('occupied', Boolean(owner));
  spotGroup.classList.remove('selected');
  spotGroup.setAttribute('aria-disabled', String(Boolean(owner)));
  spotGroup.setAttribute('aria-pressed', 'false');
  spotGroup.setAttribute('aria-label', description);
  spotGroup.querySelector('.house-spot-face')
    .setAttribute('fill', owner ? playerColor(gameState, owner) : EMPTY_SPOT_COLOR);
  spotGroup.querySelector('.house-mark').setAttribute('display', owner ? 'inline' : 'none');
  spotGroup.querySelector('title').textContent = description;
}

function createHouseSpot(gameState, city, spot, spotIndex, onSpotToggle) {
  const startAngle = -90 + spotIndex * 120;
  const [markX, markY] = pointAtAngle(city.x, city.y, MARK_RADIUS, startAngle + 60);
  const spotGroup = el('g', { class: 'house-spot', role: 'button', tabindex: 0 });
  const face = el('path', {
    class: 'house-spot-face',
    d: wedgePath(city.x, city.y, SPOT_RADIUS, startAngle, startAngle + 120),
  });
  const mark = el('path', { class: 'house-mark', d: housePath(markX, markY) });
  spotGroup.append(face, mark, el('title', {}));
  applySpotOwner(gameState, spotGroup, city.name, spot, gameState.map_houses[city.name][spot]);

  const toggle = () => onSpotToggle(city.name, spot);
  spotGroup.addEventListener('click', toggle);
  spotGroup.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      toggle();
    }
  });
  return spotGroup;
}

function drawConnections(layer, { cities, connections, minCost, maxCost }) {
  connections.forEach(({ a, b, cost }) => {
    const from = cities[a];
    const to = cities[b];
    layer.appendChild(el('line', {
      class: 'connection-line',
      x1: from.x, y1: from.y, x2: to.x, y2: to.y,
      'data-a': a, 'data-b': b,
    }));
    if (cost === 0) return;

    const x = (from.x + to.x) / 2;
    const y = (from.y + to.y) / 2;
    const label = String(cost);
    const color = costColor(cost, minCost, maxCost);
    const text = el('text', { class: 'cost-label', x, y, 'data-a': a, 'data-b': b, fill: color });
    text.textContent = label;
    layer.append(
      el('circle', {
        class: 'cost-bg', cx: x, cy: y, r: Math.max(6.5, label.length * 2.5 + 4),
        stroke: color, 'data-a': a, 'data-b': b,
      }),
      text,
    );
  });
}

function initHoverHighlight(linesLayer, citiesLayer, tooltip, gameState, { cities, neighbors }) {
  const lineElements = () => linesLayer.querySelectorAll('.connection-line, .cost-label');

  function activate(index) {
    lineElements().forEach((element) => {
      const a = +element.getAttribute('data-a');
      const b = +element.getAttribute('data-b');
      element.classList.toggle('highlight', a === index || b === index);
    });
    citiesLayer.querySelectorAll('.city-node').forEach((element) => {
      element.classList.toggle('active', +element.getAttribute('data-index') === index);
    });
  }

  function deactivate() {
    lineElements().forEach((element) => element.classList.remove('highlight'));
    citiesLayer.querySelectorAll('.city-node').forEach((element) => element.classList.remove('active'));
    tooltip.style.display = 'none';
  }

  function showTooltip(event, index) {
    const city = cities[index];
    const houseCount = Object.values(gameState.map_houses[city.name]).filter(Boolean).length;
    const heading = document.createElement('strong');
    heading.textContent = city.name;
    tooltip.replaceChildren(heading);
    [`Region: ${city.region}`, `Connections: ${neighbors.get(index).size}`, `Houses: ${houseCount}/3`]
      .forEach((detail) => tooltip.append(document.createElement('br'), detail));
    tooltip.style.display = 'block';
    tooltip.style.left = `${event.pageX + 14}px`;
    tooltip.style.top = `${event.pageY + 14}px`;
  }

  return { activate, deactivate, showTooltip };
}

// Draws the board and returns controls for the house spots; purchase rules live elsewhere.
export async function initMap(gameState) {
  const model = createMapModel(await fetchMapData());
  const { width, height, cities, connections } = model;

  const svg = document.getElementById('map');
  svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
  svg.setAttribute('width', width);
  svg.setAttribute('height', height);

  const linesLayer = el('g', { id: 'lines' });
  const citiesLayer = el('g', { id: 'cities' });
  svg.append(
    el('image', {
      class: 'map-outline', href: OUTLINE_IMAGE_URL, x: 0, y: 0, width, height, preserveAspectRatio: 'xMidYMid meet',
    }),
    el('rect', { class: 'map-boundary', x: 1, y: 1, width: width - 2, height: height - 2 }),
    linesLayer,
    citiesLayer,
  );
  drawConnections(linesLayer, model);

  const hover = initHoverHighlight(linesLayer, citiesLayer, document.getElementById('tooltip'), gameState, model);
  const spotGroups = new Map();
  let spotToggleHandler = () => {};

  cities.forEach((city, index) => {
    const cityGroup = el('g', { class: 'city-node', 'data-index': index });
    HOUSE_SPOTS.forEach((spot, spotIndex) => {
      const spotGroup = createHouseSpot(gameState, city, spot, spotIndex, (...args) => spotToggleHandler(...args));
      spotGroups.set(`${city.name}|${spot}`, spotGroup);
      cityGroup.appendChild(spotGroup);
    });

    const label = el('text', {
      class: 'city-label', x: city.x, y: city.y + 14, fill: REGION_COLORS[city.region] || '#888',
    });
    label.textContent = city.name;
    cityGroup.appendChild(label);
    citiesLayer.appendChild(cityGroup);

    cityGroup.addEventListener('mouseenter', () => hover.activate(index));
    cityGroup.addEventListener('mouseleave', hover.deactivate);
    cityGroup.addEventListener('mousemove', (event) => hover.showTooltip(event, index));
  });

  document.getElementById('stats').textContent =
    `Germany · ${cities.length} cities · ${connections.length} connections`;

  const spotGroupOf = (city, spot) => spotGroups.get(`${city}|${spot}`);
  return {
    onSpotToggle(handler) {
      spotToggleHandler = handler;
    },
    setSpotSelected(city, spot, selected) {
      const spotGroup = spotGroupOf(city, spot);
      spotGroup.classList.toggle('selected', selected);
      spotGroup.setAttribute('aria-pressed', String(selected));
    },
    setSpotOwner(city, spot, owner) {
      applySpotOwner(gameState, spotGroupOf(city, spot), city, spot, owner);
    },
  };
}
