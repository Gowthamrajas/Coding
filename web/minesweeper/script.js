const BOARD_SIZE = 10;
const MINE_COUNT = 15;

const boardEl = document.getElementById('board');
const resetBtn = document.getElementById('reset-btn');
const mineCountEl = document.getElementById('mine-count');
const flagCountEl = document.getElementById('flag-count');
const messageEl = document.getElementById('message');
const tileTemplate = document.getElementById('tile-template');

let tiles = [];
let flagsPlaced = 0;
let safeTilesLeft = 0;
let gameOver = false;
let firstReveal = true;

function buildBoard() {
  tiles = Array.from({ length: BOARD_SIZE }, (_, row) =>
    Array.from({ length: BOARD_SIZE }, (_, col) => ({
      row,
      col,
      isMine: false,
      isRevealed: false,
      isFlagged: false,
      adjacent: 0,
      element: null,
    }))
  );

  boardEl.innerHTML = '';
  boardEl.style.setProperty('--board-size', BOARD_SIZE);

  const fragment = document.createDocumentFragment();
  for (const row of tiles) {
    for (const tile of row) {
      const tileEl = tileTemplate.content.firstElementChild.cloneNode(true);
      tileEl.dataset.row = tile.row;
      tileEl.dataset.col = tile.col;
      tileEl.setAttribute('aria-label', 'Hidden tile');
      tileEl.addEventListener('click', () => handleReveal(tile));
      tileEl.addEventListener('contextmenu', (event) => {
        event.preventDefault();
        toggleFlag(tile);
      });
      tileEl.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          handleReveal(tile);
        }
        if (event.key.toLowerCase() === 'f') {
          event.preventDefault();
          toggleFlag(tile);
        }
      });
      tile.element = tileEl;
      fragment.appendChild(tileEl);
    }
  }

  boardEl.appendChild(fragment);
}

function randomizeMines(excludedTile) {
  const positions = [];
  for (let row = 0; row < BOARD_SIZE; row++) {
    for (let col = 0; col < BOARD_SIZE; col++) {
      if (excludedTile && excludedTile.row === row && excludedTile.col === col) {
        continue;
      }
      positions.push([row, col]);
    }
  }

  shuffle(positions);

  for (let i = 0; i < MINE_COUNT; i++) {
    const [row, col] = positions[i];
    tiles[row][col].isMine = true;
  }

  for (let row = 0; row < BOARD_SIZE; row++) {
    for (let col = 0; col < BOARD_SIZE; col++) {
      tiles[row][col].adjacent = countAdjacentMines(row, col);
    }
  }

  safeTilesLeft = BOARD_SIZE * BOARD_SIZE - MINE_COUNT;
  mineCountEl.textContent = MINE_COUNT.toString();
  updateFlagDisplay();
}

function shuffle(array) {
  for (let i = array.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [array[i], array[j]] = [array[j], array[i]];
  }
}

function countAdjacentMines(row, col) {
  if (tiles[row][col].isMine) {
    return 0;
  }
  return getNeighbors(row, col).reduce(
    (count, neighbor) => count + (neighbor.isMine ? 1 : 0),
    0,
  );
}

function getNeighbors(row, col) {
  const neighbors = [];
  for (let r = row - 1; r <= row + 1; r++) {
    for (let c = col - 1; c <= col + 1; c++) {
      if (r === row && c === col) continue;
      if (r < 0 || c < 0 || r >= BOARD_SIZE || c >= BOARD_SIZE) continue;
      neighbors.push(tiles[r][c]);
    }
  }
  return neighbors;
}

function handleReveal(tile) {
  if (gameOver || tile.isFlagged || tile.isRevealed) {
    return;
  }

  if (firstReveal) {
    randomizeMines(tile);
    firstReveal = false;
    messageEl.textContent = '';
  }

  if (tile.isMine) {
    revealMine(tile);
    endGame(false);
    return;
  }

  floodReveal(tile);
  if (safeTilesLeft === 0) {
    endGame(true);
  }
}

function floodReveal(startTile) {
  const queue = [startTile];

  while (queue.length > 0) {
    const tile = queue.shift();
    if (tile.isRevealed || tile.isFlagged) {
      continue;
    }

    tile.isRevealed = true;
    tile.element.classList.add('revealed');
    tile.element.setAttribute('aria-label', tile.isMine ? 'Mine' : `Revealed tile with ${tile.adjacent} nearby`);
    tile.element.textContent = tile.adjacent > 0 ? tile.adjacent : '';
    safeTilesLeft -= 1;

    if (tile.adjacent === 0) {
      for (const neighbor of getNeighbors(tile.row, tile.col)) {
        if (!neighbor.isRevealed && !neighbor.isMine) {
          queue.push(neighbor);
        }
      }
    }
  }
}

function revealMine(tile) {
  tile.isRevealed = true;
  tile.element.classList.add('revealed', 'mine');
  tile.element.textContent = '💣';
  tile.element.setAttribute('aria-label', 'Mine');

  for (const row of tiles) {
    for (const other of row) {
      if (other === tile) continue;
      if (other.isMine) {
        other.element.classList.add('revealed', 'mine');
        other.element.textContent = '💣';
        other.element.setAttribute('aria-label', 'Mine');
      }
      other.element.disabled = true;
    }
  }
}

function toggleFlag(tile) {
  if (gameOver || tile.isRevealed) {
    return;
  }

  tile.isFlagged = !tile.isFlagged;
  tile.element.classList.toggle('flagged', tile.isFlagged);
  tile.element.setAttribute('aria-label', tile.isFlagged ? 'Flagged tile' : 'Hidden tile');
  flagsPlaced += tile.isFlagged ? 1 : -1;
  updateFlagDisplay();
}

function updateFlagDisplay() {
  flagCountEl.textContent = `${flagsPlaced}/${MINE_COUNT}`;
}

function endGame(won) {
  gameOver = true;
  messageEl.textContent = won ? '🎉 Cleared! All mines avoided.' : '💥 Boom! Try again?';
  for (const row of tiles) {
    for (const tile of row) {
      tile.element.disabled = true;
      if (won && tile.isMine) {
        tile.element.classList.add('revealed', 'flagged');
        tile.element.textContent = '🚩';
        tile.element.setAttribute('aria-label', 'Mine located');
      }
      if (!won && !tile.isMine && tile.isFlagged) {
        tile.element.classList.add('revealed');
        tile.element.classList.remove('flagged');
        tile.element.textContent = '✖';
      }
    }
  }
}

function resetGame() {
  gameOver = false;
  firstReveal = true;
  flagsPlaced = 0;
  safeTilesLeft = BOARD_SIZE * BOARD_SIZE - MINE_COUNT;
  messageEl.textContent = 'Tap a tile to begin.';
  buildBoard();
  updateFlagDisplay();
}

resetBtn.addEventListener('click', () => resetGame());

resetGame();
