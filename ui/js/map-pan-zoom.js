const MIN_ZOOM = 1;
const MAX_ZOOM = 6;
const ZOOM_STEP = 1.15;
const DRAG_THRESHOLD = 4;

function clamp(value, low, high) {
  return Math.min(high, Math.max(low, value));
}

// Lets the player zoom the map with the mouse wheel and move it by dragging; the zoom and position survive redraws.
export function initMapPanZoom(svg) {
  const view = { zoom: 1, x: 0, y: 0 };
  let drag = null;
  let moved = false;

  function limitPosition() {
    const box = svg.viewBox.baseVal;

    view.x = clamp(view.x, -(view.zoom - 1) * box.width, 0);
    view.y = clamp(view.y, -(view.zoom - 1) * box.height, 0);
  }

  function apply() {
    limitPosition();
    document.getElementById('viewport').setAttribute(
      'transform',
      'translate(' + view.x + ' ' + view.y + ') scale(' + view.zoom + ')',
    );
  }

  // Converts a point on the screen into map coordinates.
  function toMap(clientX, clientY) {
    const rect = svg.getBoundingClientRect();
    const box = svg.viewBox.baseVal;

    return {
      x: (clientX - rect.left) * box.width / rect.width,
      y: (clientY - rect.top) * box.height / rect.height,
    };
  }

  svg.addEventListener('wheel', (event) => {
    event.preventDefault();

    const zoom = clamp(view.zoom * (event.deltaY < 0 ? ZOOM_STEP : 1 / ZOOM_STEP), MIN_ZOOM, MAX_ZOOM);
    const ratio = zoom / view.zoom;
    const point = toMap(event.clientX, event.clientY);

    view.x = point.x - (point.x - view.x) * ratio;
    view.y = point.y - (point.y - view.y) * ratio;
    view.zoom = zoom;
    apply();
  }, { passive: false });

  svg.addEventListener('pointerdown', (event) => {
    drag = { x: event.clientX, y: event.clientY };
    moved = false;
  });

  window.addEventListener('pointermove', (event) => {
    if (drag === null) return;

    const dx = event.clientX - drag.x;
    const dy = event.clientY - drag.y;

    if (!moved && Math.abs(dx) + Math.abs(dy) < DRAG_THRESHOLD) return;

    moved = true;
    svg.classList.add('panning');

    const rect = svg.getBoundingClientRect();
    const box = svg.viewBox.baseVal;

    view.x += dx * box.width / rect.width;
    view.y += dy * box.height / rect.height;
    drag = { x: event.clientX, y: event.clientY };
    apply();
  });

  window.addEventListener('pointerup', () => {
    drag = null;
    svg.classList.remove('panning');
  });

  // A drag ends with a click on the spot under the pointer; that click must not toggle the spot.
  svg.addEventListener('click', (event) => {
    if (moved) {
      event.stopPropagation();
      event.preventDefault();
    }
  }, true);
}
