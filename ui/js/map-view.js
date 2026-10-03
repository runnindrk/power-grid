import { el } from './dom-utils.js';
import { fetchJson } from './data-source.js';
import { requestBuyHouses, requestHousePrice } from './house-api.js';
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
  const placementStatus = document.getElementById('placement-status');
  const playerBoard = document.getElementById('player-board');
  const turnOrder = document.getElementById('turn-order');
  const players = gameState.player_turn_order;
  const playerAliases = gameState.player_aliases || {};
  const playerLabel = (player) => playerAliases[player] || player;
  const houses = gameState.map_houses;
  const currentPlayer = gameState.current_player || players[0];
  const currentAction = String(gameState.current_action || 'building_houses').replaceAll('_', ' ');
  let isBuyingHouses = false;
  let quoteRequestId = 0;
  let quotedPrice = null;
  const pendingHouses = [];

  function setPlayerPurchaseState(player, message, disabled) {
    const row = playerBoard.querySelector(`.player-row[data-player-id="${player}"]`);
    if (!row) return;
    row.querySelector('.player-house-purchase-total').textContent = message;
    row.querySelector('.player-buy-houses-button').disabled = disabled;
  }

  function clearHouseSelection(message = 'Select house spots') {
    pendingHouses.forEach(({ spotGroup }) => {
      spotGroup.classList.remove('selected');
      spotGroup.setAttribute('aria-pressed', 'false');
    });
    pendingHouses.length = 0;
    quoteRequestId += 1;
    quotedPrice = null;
    setPlayerPurchaseState(currentPlayer, message, true);
  }

  async function updateHouseQuote() {
    const requestId = ++quoteRequestId;
    quotedPrice = null;
    if (pendingHouses.length === 0) {
      setPlayerPurchaseState(currentPlayer, 'Select house spots', true);
      return;
    }

    setPlayerPurchaseState(currentPlayer, 'Calculating...', true);
    const placements = pendingHouses.map(({ city, spot }) => ({ city, spot }));
    try {
      const result = await requestHousePrice(currentPlayer, placements);
      if (requestId !== quoteRequestId) return;
      if (result.error_code !== 0) throw new Error('House price request failed');
      quotedPrice = result.price;
      setPlayerPurchaseState(currentPlayer, `Total $${result.price}`, false);
    } catch (error) {
      if (requestId !== quoteRequestId) return;
      setPlayerPurchaseState(currentPlayer, error.message, true);
    }
  }

  playerBoard.addEventListener('click', async (event) => {
    const buyButton = event.target.closest('.player-buy-houses-button');
    if (!buyButton || isBuyingHouses || pendingHouses.length === 0) return;
    const buyer = buyButton.closest('.player-house-purchase-controls').dataset.playerId;
    if (buyer !== currentPlayer || quotedPrice === null) return;
    isBuyingHouses = true;
    setPlayerPurchaseState(currentPlayer, 'Buying houses...', true);
    const placements = pendingHouses.map(({ city, spot }) => ({ city, spot }));
    try {
      const result = await requestBuyHouses(buyer, placements);
      if (result.error_code !== 0) throw new Error('House purchase failed');
      pendingHouses.forEach(({ city, spot, spotGroup }) => {
        houses[city][spot] = buyer;
        updateSpot(spotGroup, city, spot, buyer);
      });
      gameState.player_money[buyer] -= result.price;
      updatePlayerBoard(gameState);
      const houseCount = pendingHouses.length;
      clearHouseSelection(`Bought ${houseCount} ${houseCount === 1 ? 'house' : 'houses'} for $${result.price}`);
      placementStatus.textContent = `Houses placed for ${playerLabel(buyer)}`;
    } catch (error) {
      setPlayerPurchaseState(currentPlayer, error.message, quotedPrice === null);
    } finally {
      isBuyingHouses = false;
    }
  });

  turnOrder.replaceChildren(document.createTextNode('Turn order: '));
  players.forEach((player, index) => {
    if (index > 0) turnOrder.appendChild(document.createTextNode(' → '));
    const playerTurn = document.createElement('span');
    const isCurrentPlayer = player === currentPlayer;
    playerTurn.className = `turn-order-player${isCurrentPlayer ? ' current' : ''}`;
    playerTurn.textContent = playerLabel(player);
    playerTurn.style.color = PLAYER_COLORS[index % PLAYER_COLORS.length];
    if (isCurrentPlayer) playerTurn.setAttribute('aria-current', 'true');
    turnOrder.appendChild(playerTurn);
  });
  placementStatus.textContent = `${currentAction} · ${playerLabel(currentPlayer)}`;

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
        class: `house-spot${occupiedSpots[spot] ? ' occupied' : ''}`,
        role: 'button', tabindex: 0,
        'aria-label': `${city.name}, ${spot.replace('_', ' ')}: ${playerLabel(occupiedSpots[spot]) || 'empty'}`,
        'aria-disabled': String(Boolean(occupiedSpots[spot])),
        'aria-pressed': 'false',
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
      title.textContent = `${city.name} ${spot.replace('_', ' ')}: ${playerLabel(occupiedSpots[spot]) || 'empty'}`;
      spotGroup.append(face, mark, title);

      const toggleHouseSelection = () => {
        if (isBuyingHouses || occupiedSpots[spot]) return;
        const existingIndex = pendingHouses.findIndex((house) => house.city === city.name && house.spot === spot);
        if (existingIndex >= 0) {
          pendingHouses.splice(existingIndex, 1);
        } else {
          pendingHouses.push({ city: city.name, spot, spotGroup });
        }
        const isSelected = existingIndex < 0;
        spotGroup.classList.toggle('selected', isSelected);
        spotGroup.setAttribute('aria-pressed', String(isSelected));
        updateHouseQuote();
      };
      spotGroup.addEventListener('click', toggleHouseSelection);
      spotGroup.addEventListener('keydown', (evt) => {
        if (evt.key === 'Enter' || evt.key === ' ') {
          evt.preventDefault();
          toggleHouseSelection();
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
    const label = `${cityName}, ${spot.replace('_', ' ')}: ${playerLabel(owner) || 'empty'}`;
    spotGroup.classList.toggle('occupied', Boolean(owner));
    spotGroup.classList.remove('selected');
    spotGroup.setAttribute('aria-disabled', String(Boolean(owner)));
    spotGroup.setAttribute('aria-pressed', 'false');
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
    `Germany · ${cities.length} cities · ${connections.length} connections`;
}
