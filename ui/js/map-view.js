import { el } from './dom-utils.js';
import { postHouseSpot } from './api.js';

function setHighlight(ids, on) {
  for (const id of ids) {
    document.getElementById(id).classList.toggle('highlight', on);
  }
}

function setNetworkHighlight(spot, on) {
  for (const id of spot.network_path_ids) {
    const lines = document.querySelectorAll('[data-connection-id="' + id + '"]');

    for (const line of lines) {
      line.classList.toggle('network-highlight', on);

      if (on) {
        line.style.setProperty('--network-color', spot.network_color);
      } else {
        line.style.removeProperty('--network-color');
      }
    }
  }
}

function showPriceTooltip(tooltip, spot, event) {
  tooltip.textContent = spot.connection_cost === null
    ? '$' + spot.price + ' + connection unavailable'
    : '$' + spot.price + ' + $' + spot.connection_cost + ' connection = $' + spot.total_price;
  tooltip.style.display = 'block';
  tooltip.style.left = (event.pageX + 14) + 'px';
  tooltip.style.top = (event.pageY + 14) + 'px';
}

function createSelectionPattern(color) {
  const definitions = el('defs', {});
  const pattern = el('pattern', {
    id: 'selected-house-pattern',
    width: 8,
    height: 8,
    patternUnits: 'userSpaceOnUse',
  });

  pattern.append(
    el('rect', { width: 8, height: 8, fill: color }),
    el('path', {
      d: 'M -2 2 L 2 -2 M 0 8 L 8 0 M 6 10 L 10 6',
      fill: 'none',
      stroke: '#fff',
      'stroke-opacity': 0.7,
      'stroke-width': 1.5,
    }),
  );
  definitions.appendChild(pattern);

  return definitions;
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
  const faceFill = spot.classes.includes('selected') ? 'url(#selected-house-pattern)' : spot.face_fill;
  const face = el('path', { class: 'house-spot-face', d: spot.face_path, fill: faceFill });

  group.append(face);

  group.addEventListener('mouseenter', (event) => {
    showPriceTooltip(tooltip, spot, event);
    setNetworkHighlight(spot, true);
  });
  group.addEventListener('mousemove', (event) => showPriceTooltip(tooltip, spot, event));
  group.addEventListener('mouseleave', () => {
    tooltip.style.display = 'none';
    setNetworkHighlight(spot, false);
  });
  group.addEventListener('focus', () => setNetworkHighlight(spot, true));
  group.addEventListener('blur', () => setNetworkHighlight(spot, false));

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

  const label = el('text', { class: 'city-label', x: city.x, y: city.label_y, fill: city.label_color });

  label.textContent = city.name;
  group.appendChild(label);

  for (const spot of city.spots) {
    const houseSpot = createHouseSpot(spot, tooltip, refresh, gameStarted);

    group.insertBefore(houseSpot, label);
    houseSpot.addEventListener('mouseenter', () => group.insertBefore(houseSpot, label));
    houseSpot.addEventListener('focus', () => group.insertBefore(houseSpot, label));
  }

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
      'data-connection-id': line.id,
      x1: line.x1, y1: line.y1, x2: line.x2, y2: line.y2,
    }));

    const networkColors = line.network_colors || [];
    const length = Math.hypot(line.x2 - line.x1, line.y2 - line.y1) || 1;
    const normalX = -(line.y2 - line.y1) / length;
    const normalY = (line.x2 - line.x1) / length;

    for (let index = 0; index < networkColors.length; index++) {
      const network = networkColors[index];
      const laneWidth = networkColors.length === 1 ? 3.5 : Math.min(2, 6 / networkColors.length);
      const offset = (index - (networkColors.length - 1) / 2) * laneWidth;
      const segment = el('line', {
        class: line.classes.join(' ') + ' network-segment',
        id: line.id + '-network-' + network.player,
        'data-connection-id': line.id,
        x1: line.x1 + normalX * offset,
        y1: line.y1 + normalY * offset,
        x2: line.x2 + normalX * offset,
        y2: line.y2 + normalY * offset,
      });

      segment.style.setProperty('--segment-color', network.color);
      segment.style.setProperty('--segment-width', laneWidth);
      layer.appendChild(segment);
    }
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

  viewport.replaceChildren(
    createSelectionPattern(map.selection_color),
    outline,
    boundary,
    createLines(map),
    cities,
  );

  document.getElementById('stats').textContent = map.stats;
}
