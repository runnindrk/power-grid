import { el } from './dom-utils.js';
import { postHouseSpot } from './api.js';

function setHighlight(ids, on) {
  for (const id of ids) {
    document.getElementById(id).classList.toggle('highlight', on);
  }
}

function showPriceTooltip(tooltip, spot, event) {
  tooltip.textContent = '$' + spot.price;
  tooltip.style.display = 'block';
  tooltip.style.left = (event.pageX + 14) + 'px';
  tooltip.style.top = (event.pageY + 14) + 'px';
}

function createHouseSpot(spot, tooltip, refresh, gameStarted) {
  const disabled = spot.aria_disabled || !gameStarted;
  const group = el('g', {
    class: spot.classes.join(' '),
    role: 'button',
    tabindex: disabled ? -1 : 0,
    'aria-label': spot.aria_label,
    'aria-disabled': disabled,
    'aria-pressed': spot.aria_pressed,
  });
  const face = el('path', { class: 'house-spot-face', d: spot.face_path, fill: spot.face_fill });
  const mark = el('path', { class: 'house-mark', d: spot.mark_path, display: spot.mark_display });

  group.append(face, mark);

  group.addEventListener('mouseenter', (event) => showPriceTooltip(tooltip, spot, event));
  group.addEventListener('mousemove', (event) => showPriceTooltip(tooltip, spot, event));
  group.addEventListener('mouseleave', () => {
    tooltip.style.display = 'none';
  });

  function toggleSpot() {
    if (disabled) return;

    postHouseSpot(spot.city, spot.spot).then(refresh);
  }

  group.addEventListener('click', toggleSpot);
  group.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();

      toggleSpot();
    }
  });

  return group;
}

function createCity(city, tooltip, refresh, gameStarted) {
  const group = el('g', {
    class: city.classes.join(' '),
    'data-index': city.index,
    'aria-disabled': city.aria_disabled,
  });

  for (const spot of city.spots) {
    group.appendChild(createHouseSpot(spot, tooltip, refresh, gameStarted));
  }

  const label = el('text', { class: 'city-label', x: city.x, y: city.label_y, fill: city.label_color });

  label.textContent = city.name;
  group.appendChild(label);

  group.addEventListener('mouseenter', () => {
    group.classList.add('active');
    setHighlight(city.highlight_ids, true);
  });

  group.addEventListener('mouseleave', () => {
    group.classList.remove('active');
    setHighlight(city.highlight_ids, false);
  });

  return group;
}

function createLines(map) {
  const layer = el('g', { id: 'lines' });

  for (const line of map.lines) {
    layer.appendChild(el('line', {
      class: line.classes.join(' '), id: line.id,
      x1: line.x1, y1: line.y1, x2: line.x2, y2: line.y2,
    }));
  }

  for (const label of map.cost_labels) {
    layer.appendChild(el('circle', {
      class: label.inactive ? 'cost-bg inactive' : 'cost-bg',
      cx: label.x, cy: label.y, r: label.radius, stroke: label.color,
    }));

    const text = el('text', {
      class: label.inactive ? 'cost-label inactive' : 'cost-label',
      id: label.id, x: label.x, y: label.y, fill: label.color,
    });

    text.textContent = label.text;
    layer.appendChild(text);
  }

  return layer;
}

export function renderMap(map, refresh, gameStarted) {
  const svg = document.getElementById('map');

  svg.setAttribute('viewBox', '0 0 ' + map.width + ' ' + map.height);
  svg.setAttribute('width', map.width);
  svg.setAttribute('height', map.height);

  const outline = el('image', {
    class: 'map-outline',
    href: map.outline_url,
    x: 0,
    y: 0,
    width: map.width,
    height: map.height,
    preserveAspectRatio: 'xMidYMid meet',
  });
  const boundary = el('rect', {
    class: 'map-boundary',
    x: map.boundary.x,
    y: map.boundary.y,
    width: map.boundary.width,
    height: map.boundary.height,
  });
  const tooltip = document.getElementById('tooltip');
  const cities = el('g', { id: 'cities' });

  for (const city of map.cities) {
    cities.appendChild(createCity(city, tooltip, refresh, gameStarted));
  }

  let viewport = document.getElementById('viewport');

  if (viewport === null) {
    viewport = el('g', { id: 'viewport' });
    svg.appendChild(viewport);
  }

  viewport.replaceChildren(outline, boundary, createLines(map), cities);

  document.getElementById('stats').textContent = map.stats;
}
