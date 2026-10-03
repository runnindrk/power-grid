export const REGION_COLORS = {
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

const lerp = (a, b, t) => Math.round(a + (b - a) * t);

export function costColor(cost, min, max) {
  if (max === min) return `rgb(${COST_MID.join(',')})`;
  const t = (cost - min) / (max - min);
  const [from, to, localT] = t < 0.5 ? [COST_LOW, COST_MID, t * 2] : [COST_MID, COST_HIGH, (t - 0.5) * 2];
  return `rgb(${from.map((c, i) => lerp(c, to[i], localT)).join(',')})`;
}

export function pointAtAngle(cx, cy, radius, angle) {
  const radians = (angle * Math.PI) / 180;
  return [cx + Math.cos(radians) * radius, cy + Math.sin(radians) * radius];
}

export function wedgePath(cx, cy, radius, startAngle, endAngle) {
  const [startX, startY] = pointAtAngle(cx, cy, radius, startAngle);
  const [endX, endY] = pointAtAngle(cx, cy, radius, endAngle);
  return `M ${cx} ${cy} L ${startX} ${startY} A ${radius} ${radius} 0 0 1 ${endX} ${endY} Z`;
}

export function housePath(cx, cy) {
  return `M ${cx - 4} ${cy} L ${cx} ${cy - 3.5} L ${cx + 4} ${cy} V ${cy + 4} H ${cx + 1.5} V ${cy + 1} H ${cx - 1.5} V ${cy + 4} H ${cx - 4} Z`;
}
