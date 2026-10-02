import { el } from './dom-utils.js';
import { fetchJson } from './data-source.js';
import { requestHousePlacement } from './house-api.js';
import { createMapModel, MAP_DATA_URL, OUTLINE_IMAGE_URL } from './map-model.js';
import { updatePlayerBoard } from './player-board.js';

const PLAYER_COLORS = ['#e85d5d', '#519cde', '#43a047', '#fb8c00', '#9445aa', '#fdd835'];
const HOUSE_SPOTS = ['spot_1', 'spot_2', 'spot_3'];

const regionColors = {
  Green: '#43a047',
  Orange: '#fb8c00',
  Red: '#e53935',
  Yellow: '#fdd835',
  Blue: '#519cde',
  Purple: '#9445aa',
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

function wedgePath(cx, cy, radius, startAngle, endAngle) {
  const point = (angle) => {
    const radians = (angle * Math.PI) / 180;
    return [cx + Math.cos(radians) * radius, cy + Math.sin(radians) * radius];
  };
  const [startX, startY] = point(startAngle);
  const [endX, endY] = point(endAngle);
  return `M ${cx} ${cy} L ${startX} ${startY} A ${radius} ${radius} 0 0 1 ${endX} ${endY} Z`;
}

function housePath(cx, cy) {
  return `M ${cx - 4} ${cy} L ${cx} ${cy - 3.5} L ${cx + 4} ${cy} V ${cy + 4} H ${cx + 1.5} V ${cy + 1} H ${cx - 1.5} V ${cy + 4} H ${cx - 4} Z`;
}

export async function initMap(gameState) {
  const model = createMapModel(await fetchJson(MAP_DATA_URL));
  const { width, height, cities, connections, neighbors, minCost, maxCost } = model;

  const svg = document.getElementById('map');
  const tooltip = document.getElementById('tooltip');
  const playerSelect = document.getElementById('player-select');
  const placementStatus = document.getElementById('placement-status');
  const players = gameState.player_turn_order;
  const houses = gameState.map_houses;
  let selectedPlayer = players[0];
  let isSavingHouse = false;

  players.forEach((player, index) => {
    const option = document.createElement('option');
    option.value = player;
    option.textContent = player;
    option.style.color = PLAYER_COLORS[index % PLAYER_COLORS.length];
    playerSelect.appendChild(option);
  });
  playerSelect.addEventListener('change', () => {
    selectedPlayer = playerSelect.value;
    placementStatus.textContent = `Editing houses for ${selectedPlayer}`;
  });
  placementStatus.textContent = `Editing houses for ${selectedPlayer}`;

  svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
  svg.setAttribute('width', width);
  svg.setAttribute('height', height);

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

  cities.forEach((city, i) => {
    const cityGroup = el('g', { class: 'city-node', 'data-index': i });
    const occupiedSpots = houses[city.name];

    HOUSE_SPOTS.forEach((spot, spotIndex) => {
      const startAngle = -90 + spotIndex * 120;
      const endAngle = startAngle + 120;
      const middleAngle = (startAngle + endAngle) / 2;
      const markRadius = 5.5;
      const markX = city.x + Math.cos((middleAngle * Math.PI) / 180) * markRadius;
      const markY = city.y + Math.sin((middleAngle * Math.PI) / 180) * markRadius;
      const spotGroup = el('g', {
        class: 'house-spot', role: 'button', tabindex: 0,
        'aria-label': `${city.name}, ${spot.replace('_', ' ')}: ${occupiedSpots[spot] || 'empty'}`,
      });
      const face = el('path', {
        class: 'house-spot-face',
        d: wedgePath(city.x, city.y, 11, startAngle, endAngle),
        fill: occupiedSpots[spot] ? playerColor(occupiedSpots[spot]) : '#30343b',
      });
      const mark = el('path', {
        class: 'house-mark', d: housePath(markX, markY),
        display: occupiedSpots[spot] ? 'inline' : 'none',
      });
      const title = el('title', {});
      title.textContent = `${city.name} ${spot.replace('_', ' ')}: ${occupiedSpots[spot] || 'empty'}`;
      spotGroup.append(face, mark, title);

      const activateSpot = async () => {
        if (isSavingHouse) return;

        isSavingHouse = true;
        playerSelect.disabled = true;
        placementStatus.textContent = 'Saving house placement';
        try {
          const expectedOwner = occupiedSpots[spot] === selectedPlayer ? null : selectedPlayer;
          const updatedState = await requestHousePlacement(selectedPlayer, city.name, spot);
          if (updatedState.map_houses?.[city.name]?.[spot] !== expectedOwner) {
            throw new Error('Server response did not confirm the house placement');
          }
          houses[city.name][spot] = updatedState.map_houses[city.name][spot];
          updateSpot(spotGroup, city.name, spot, houses[city.name][spot]);
          updatePlayerBoard(updatedState);
          placementStatus.textContent = expectedOwner
            ? `Placed ${selectedPlayer}'s house in ${city.name}`
            : `Removed ${selectedPlayer}'s house from ${city.name}`;
        } catch (error) {
          placementStatus.textContent = error.message;
        } finally {
          isSavingHouse = false;
          playerSelect.disabled = false;
        }
      };
      spotGroup.addEventListener('click', activateSpot);
      spotGroup.addEventListener('keydown', (evt) => {
        if (evt.key === 'Enter' || evt.key === ' ') {
          evt.preventDefault();
          activateSpot();
        }
      });
      cityGroup.appendChild(spotGroup);
    });

    const label = el('text', {
      class: 'city-label', x: city.x, y: city.y + 14,
      fill: regionColors[city.region] || '#888',
    });
    label.textContent = city.name;
    cityGroup.appendChild(label);
    citiesLayer.appendChild(cityGroup);

    cityGroup.addEventListener('mouseenter', () => setActive(i));
    cityGroup.addEventListener('mouseleave', clearActive);
    cityGroup.addEventListener('mousemove', (evt) => showTooltip(evt, city));
  });

  function playerColor(player) {
    const playerIndex = players.indexOf(player);
    return PLAYER_COLORS[(playerIndex < 0 ? 0 : playerIndex) % PLAYER_COLORS.length];
  }

  function updateSpot(spotGroup, cityName, spot, owner) {
    const label = `${cityName}, ${spot.replace('_', ' ')}: ${owner || 'empty'}`;
    spotGroup.querySelector('.house-spot-face').setAttribute('fill', owner ? playerColor(owner) : '#30343b');
    spotGroup.querySelector('.house-mark').setAttribute('display', owner ? 'inline' : 'none');
    spotGroup.setAttribute('aria-label', label);
    spotGroup.querySelector('title').textContent = label;
  }

  function setActive(i) {
    linesLayer.querySelectorAll('.connection-line, .cost-label').forEach((elm) => {
      const a = +elm.getAttribute('data-a'), b = +elm.getAttribute('data-b');
      elm.classList.toggle('highlight', a === i || b === i);
    });

    citiesLayer.querySelectorAll('.city-node').forEach((elm) => {
      elm.classList.toggle('active', +elm.getAttribute('data-index') === i);
    });
  }

  function clearActive() {
    linesLayer.querySelectorAll('.connection-line, .cost-label').forEach((elm) => elm.classList.remove('highlight'));
    citiesLayer.querySelectorAll('.city-node').forEach((elm) => elm.classList.remove('active'));
    tooltip.style.display = 'none';
  }

  function showTooltip(evt, city) {
    const neighborCount = neighbors.get(cities.indexOf(city)).size;
    const houseCount = Object.values(houses[city.name]).filter(Boolean).length;
    tooltip.style.display = 'block';
    tooltip.style.left = (evt.pageX + 14) + 'px';
    tooltip.style.top = (evt.pageY + 14) + 'px';
    const heading = document.createElement('strong');
    heading.textContent = city.name;
    tooltip.replaceChildren(heading);
    [`Region: ${city.region}`, `Connections: ${neighborCount}`, `Houses: ${houseCount}/3`]
      .forEach((detail) => tooltip.append(document.createElement('br'), detail));
  }

  document.getElementById('stats').textContent =
    `${cities.length} cities · ${connections.length} connections`;
}
