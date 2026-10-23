import { fetchSavedGames, postLoadGame, postNewGame } from './api.js';

const form = document.getElementById('new-game-form');
const playerCount = document.getElementById('player-count');
const newGameButton = document.getElementById('new-game');
const savedGamesPanel = document.getElementById('saved-games-panel');
const savedGamesList = document.getElementById('saved-games-list');
const status = document.getElementById('setup-status');
let savedGames = [];

function showMessage(result) {
  status.textContent = result.message;
  status.dataset.state = result.status;
}

async function enterGame(action) {
  newGameButton.disabled = true;
  savedGamesList.querySelectorAll('button').forEach((button) => {
    button.disabled = true;
  });

  const result = await action();
  showMessage(result);

  if (result.status === 'ok') {
    window.location.assign('/ui/map.html');
    return;
  }

  newGameButton.disabled = false;
  await refreshSavedGames();
}

function formatSavedAt(value) {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value));
}

function renderSavedGames() {
  savedGamesList.replaceChildren();

  if (savedGames.length === 0) {
    const empty = document.createElement('li');

    empty.className = 'saved-games-empty';
    empty.textContent = 'No saved games found.';
    savedGamesList.appendChild(empty);
    return;
  }

  for (const save of savedGames) {
    const item = document.createElement('li');
    const button = document.createElement('button');
    const details = document.createElement('span');
    const timestamp = document.createElement('time');

    item.className = 'saved-game-item';
    button.className = 'saved-game-load';
    button.type = 'button';
    button.setAttribute(
      'aria-label',
      `Load saved game from ${formatSavedAt(save.saved_at)}, ${save.number_of_players} players`,
    );
    details.className = 'saved-game-details';
    timestamp.dateTime = save.saved_at;
    timestamp.textContent = formatSavedAt(save.saved_at);
    details.append(
      timestamp,
      document.createTextNode(`${save.number_of_players} players`),
    );
    button.appendChild(details);
    button.addEventListener('click', () => {
      enterGame(() => postLoadGame(save.id));
    });
    item.appendChild(button);
    savedGamesList.appendChild(item);
  }
}

async function refreshSavedGames() {
  savedGames = await fetchSavedGames();
  renderSavedGames();
}

form.addEventListener('submit', (event) => {
  event.preventDefault();

  if (!form.reportValidity()) return;

  enterGame(() => postNewGame(Number(playerCount.value)));
});

refreshSavedGames();