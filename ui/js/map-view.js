import { el } from './dom-utils.js';

const MAP_DATA_URL = '../../game_info/maps/germany/power_grid_germany_map.json';
const OUTLINE_IMAGE_URL = '../../game_info/maps/germany/germany_outline.jpg';
const SCALE = 1.25;

const regionColors = {
  Green: '#43a047',
  Orange: '#fb8c00',
  Red: '#e53935',
  Yellow: '#fdd835',
  Blue: '#1e88e5',
  Purple: '#8e24aa',
};

// Low costs read brownish, mid costs grey, high costs yellow.
const COST_LOW = [141, 85, 36];
const COST_MID = [154, 160, 166];
const COST_HIGH = [255, 213, 79];

function lerp(a, b, t) {
  return Math.round(a + (b - a) * t);
}

function costColor(cost, min, max) {
  if (max === min) return `rgb(${COST_MID.join(',')})`;
  const t = (cost - min) / (max - min);
  const [from, to, localT] = t < 0.5 ? [COST_LOW, COST_MID, t * 2] : [COST_MID, COST_HIGH, (t - 0.5) * 2];
  const rgb = from.map((c, i) => lerp(c, to[i], localT));
  return `rgb(${rgb.join(',')})`;
}

export async function initMap() {
  const res = await fetch(MAP_DATA_URL);
  const data = await res.json();

  const [width, height] = data.map_size[0].map((v) => v * SCALE);
  const cities = data.cities_positions.map(([name, region, x, y]) => ({ name, region, x: x * SCALE, y: y * SCALE }));
  // Rows may interleave "<cost>, <cityName>" pairs to ease manual editing; strip the names back out.
  const matrix = data.connection_matrix.map((row) => row.filter((v) => typeof v !== 'string'));

  const svg = document.getElementById('map');
  svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
  svg.setAttribute('width', width);
  svg.setAttribute('height', height);

  // Build unique connection list (i < j) from the matrix, tolerating asymmetric entries.
  const connections = [];
  for (let i = 0; i < matrix.length; i++) {
    for (let j = i + 1; j < matrix.length; j++) {
      const cost = matrix[i][j] ?? matrix[j][i];
      if (cost !== null && cost !== undefined) {
        connections.push({ a: i, b: j, cost });
      }
    }
  }

  const costValues = connections.map((c) => c.cost).filter((c) => c !== 0);
  const minCost = Math.min(...costValues);
  const maxCost = Math.max(...costValues);

  const boundary = el('rect', {
    class: 'map-boundary', x: 1, y: 1, width: width - 2, height: height - 2,
  });

  const outline = el('image', {
    class: 'map-outline', href: OUTLINE_IMAGE_URL, x: 0, y: 0, width, height, preserveAspectRatio: 'xMidYMid meet',
  });
  svg.appendChild(outline);
  svg.appendChild(boundary);

  const linesLayer = el('g', { id: 'lines' });
  const citiesLayer = el('g', { id: 'cities' });
  svg.appendChild(linesLayer);
  svg.appendChild(citiesLayer);

  const neighborMap = new Map(cities.map((_, i) => [i, new Set()]));
  connections.forEach(({ a, b }) => {
    neighborMap.get(a).add(b);
    neighborMap.get(b).add(a);
  });

  connections.forEach(({ a, b, cost }) => {
    const ca = cities[a], cb = cities[b];
    const line = el('line', {
      class: 'connection-line',
      x1: ca.x, y1: ca.y, x2: cb.x, y2: cb.y,
      'data-a': a, 'data-b': b,
    });
    linesLayer.appendChild(line);

    if (cost === 0) return;

    const mx = (ca.x + cb.x) / 2;
    const my = (ca.y + cb.y) / 2;
    const label = String(cost);
    const color = costColor(cost, minCost, maxCost);
    const bg = el('circle', {
      class: 'cost-bg', cx: mx, cy: my, r: Math.max(6.5, label.length * 2.5 + 4),
      stroke: color, 'data-a': a, 'data-b': b,
    });
    const text = el('text', {
      class: 'cost-label', x: mx, y: my, 'data-a': a, 'data-b': b,
      fill: color,
    });
    text.textContent = label;
    linesLayer.appendChild(bg);
    linesLayer.appendChild(text);
  });

  const tooltip = document.getElementById('tooltip');

  cities.forEach((city, i) => {
    const dot = el('circle', {
      class: 'city-dot', cx: city.x, cy: city.y, r: 11,
      fill: regionColors[city.region] || '#888', 'data-index': i,
    });
    const label = el('text', {
      class: 'city-label', x: city.x, y: city.y + 12,
    });
    label.textContent = city.name;
    citiesLayer.appendChild(dot);
    citiesLayer.appendChild(label);

    dot.addEventListener('mouseenter', () => setActive(i));
    dot.addEventListener('mouseleave', clearActive);
    dot.addEventListener('mousemove', (evt) => showTooltip(evt, city));
  });

  function setActive(i) {
    document.querySelectorAll('.connection-line, .cost-label').forEach((elm) => {
      const a = +elm.getAttribute('data-a'), b = +elm.getAttribute('data-b');
      elm.classList.toggle('highlight', a === i || b === i);
    });
    document.querySelectorAll('.city-dot').forEach((elm) => {
      elm.classList.toggle('active', +elm.getAttribute('data-index') === i);
    });
  }

  function clearActive() {
    document.querySelectorAll('.connection-line, .cost-label').forEach((elm) => elm.classList.remove('highlight'));
    document.querySelectorAll('.city-dot').forEach((elm) => elm.classList.remove('active'));
    tooltip.style.display = 'none';
  }

  function showTooltip(evt, city) {
    const neighborCount = neighborMap.get(cities.indexOf(city)).size;
    tooltip.style.display = 'block';
    tooltip.style.left = (evt.pageX + 14) + 'px';
    tooltip.style.top = (evt.pageY + 14) + 'px';
    tooltip.innerHTML = `<strong>${city.name}</strong><br>Region: ${city.region}<br>Connections: ${neighborCount}`;
  }

  document.getElementById('stats').textContent =
    `${cities.length} cities · ${connections.length} connections`;
}
