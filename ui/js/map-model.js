export const MAP_DATA_URL = '../../game_info/maps/germany/power_grid_germany_map.json';
export const OUTLINE_IMAGE_URL = '../../game_info/maps/germany/germany_outline.jpg';
export const MAP_SCALE = 1.25;

export function createMapModel(data) {
  const [width, height] = data.map_size[0].map((dimension) => dimension * MAP_SCALE);
  const cities = data.cities_positions.map(([name, region, x, y]) => ({
    name,
    region,
    x: x * MAP_SCALE,
    y: y * MAP_SCALE,
  }));

  // City names are interleaved with matrix values for readability in the JSON file.
  const matrix = data.connection_matrix.map((row) => row.filter((value) => typeof value !== 'string'));
  const connections = [];
  const neighbors = new Map(cities.map((_, index) => [index, new Set()]));

  for (let first = 0; first < matrix.length; first += 1) {
    for (let second = first + 1; second < matrix.length; second += 1) {
      const cost = matrix[first][second] ?? matrix[second][first];
      if (cost === null || cost === undefined) continue;

      connections.push({ a: first, b: second, cost });
      neighbors.get(first).add(second);
      neighbors.get(second).add(first);
    }
  }

  const costs = connections.map(({ cost }) => cost).filter((cost) => cost !== 0);

  return {
    width,
    height,
    cities,
    connections,
    neighbors,
    minCost: Math.min(...costs),
    maxCost: Math.max(...costs),
  };
}
