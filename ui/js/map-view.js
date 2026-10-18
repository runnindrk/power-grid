import { el } from './dom-utils.js';
import { postHouseSpot } from './api.js';

function setHighlight(ids, on) {
  for (const id of ids) {
    document.getElementById(id).classList.toggle('highlight', on);
  }
}

function showTooltip(tooltip, city, event) {
  const title = document.createElement('strong');

  title.textContent = city.tooltip.title;
  tooltip.replaceChildren(title);

  for (const line of city.tooltip.lines) {
    tooltip.append(document.createElement('br'), line);
  }

  tooltip.style.display = 'block';
  tooltip.style.left = (event.pageX + 14) + 'px';
  tooltip.style.top = (event.pageY + 14) + 'px';
}

function createHouseSpot(spot, refresh) {
  const group = el('g', {
    class: spot.classes.join(' '),
    role: 'button',
    tabindex: 0,
    'aria-label': spot.aria_label,
    'aria-disabled': spot.aria_disabled,
    'aria-pressed': spot.aria_pressed,
  });
  const face = el('path', { class: 'house-spot-face', d: spot.face_path, fill: spot.face_fill });
  const mark = el('path', { class: 'house-mark', d: spot.mark_path, display: spot.mark_display });
  const title = el('title', {});

  title.textContent = spot.aria_label;
  group.append(face, mark, title);

  function toggleSpot() {
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

function createCity(city, tooltip, refresh) {
  const group = el('g', { class: 'city-node', 'data-index': city.index });

  for (const spot of city.spots) {
    group.appendChild(createHouseSpot(spot, refresh));
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

    tooltip.style.display = 'none';
  });

  group.addEventListener('mousemove', (event) => showTooltip(tooltip, city, event));

  return group;
}

function createLines(map) {
  const layer = el('g', { id: 'lines' });

  for (const line of map.lines) {
    layer.appendChild(el('line', {
      class: 'connection-line', id: line.id, x1: line.x1, y1: line.y1, x2: line.x2, y2: line.y2,
    }));
  }

  for (const label of map.cost_labels) {
    layer.appendChild(el('circle', {
      class: 'cost-bg', cx: label.x, cy: label.y, r: label.radius, stroke: label.color,
    }));

    const text = el('text', { class: 'cost-label', id: label.id, x: label.x, y: label.y, fill: label.color });

    text.textContent = label.text;
    layer.appendChild(text);
  }

  return layer;
}

export function renderMap(map, refresh) {
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
    cities.appendChild(createCity(city, tooltip, refresh));
  }

  svg.replaceChildren(outline, boundary, createLines(map), cities);

  document.getElementById('stats').textContent = map.stats;
}
