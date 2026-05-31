"""Minesweeper — first-click-safe, BFS flood reveal, three difficulties.

Exposes run(stdscr, theme) for the launcher. Returns the (possibly changed)
theme name so the launcher remembers the player's choice.
"""

import curses
import random
import time

from common import themes

NAME = "Minesweeper"
DESC = "Clear the grid without detonating a mine."

DIFFICULTIES = {"easy": (9, 9, 10), "medium": (16, 16, 40), "hard": (16, 30, 99)}
HIDDEN, REVEALED, FLAGGED = 0, 1, 2

# Game-local color pairs (1..50 range is free for games to use).
P_NUM = {n: n for n in range(1, 9)}   # counts 1..8 -> pairs 1..8
P_HIDDEN, P_FLAG, P_MINE = 9, 10, 11
P_CURSOR_H, P_CURSOR_R, P_CURSOR_F = 12, 13, 14
P_EMPTY, P_WIN, P_LOSE = 15, 16, 17


def apply_theme(stdscr, name):
    p = themes.palette(name)
    c = themes.color
    bg = c(p["bg"])
    for i in range(1, 9):
        curses.init_pair(i, c(p["accents"][i - 1]), bg)
    curses.init_pair(P_HIDDEN,   c(p["dim"]),  c(p["surface"]))
    curses.init_pair(P_FLAG,     c(p["yellow"]), c(p["surface"]))
    curses.init_pair(P_MINE,     c(p["fg"]),   c(p["red"]))
    curses.init_pair(P_CURSOR_H, c(p["bg"]),   c(p["accents"][0]))
    curses.init_pair(P_CURSOR_R, c(p["bg"]),   c(p["accents"][0]))
    curses.init_pair(P_CURSOR_F, c(p["yellow"]), c(p["accents"][0]))
    curses.init_pair(P_EMPTY,    bg, bg)
    curses.init_pair(P_WIN,      c(p["bg"]),   c(p["green"]))
    curses.init_pair(P_LOSE,     c(p["fg"]),   c(p["red"]))
    themes.apply_chrome(stdscr, name)


# --------------------------------------------------------------------------
# Pure game logic
# --------------------------------------------------------------------------
def make_board(rows, cols, mines, safe_r, safe_c):
    safe = {(safe_r + dr, safe_c + dc)
            for dr in range(-1, 2) for dc in range(-1, 2)
            if 0 <= safe_r + dr < rows and 0 <= safe_c + dc < cols}
    candidates = [(r, c) for r in range(rows) for c in range(cols) if (r, c) not in safe]
    mine_set = set(random.sample(candidates, min(mines, len(candidates))))
    grid = [[0] * cols for _ in range(rows)]
    for r, c in mine_set:
        grid[r][c] = -1
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == -1:
                continue
            grid[r][c] = sum(1 for dr in range(-1, 2) for dc in range(-1, 2)
                             if 0 <= r + dr < rows and 0 <= c + dc < cols
                             and grid[r + dr][c + dc] == -1)
    return grid, mine_set


def flood_reveal(grid, state, rows, cols, r, c):
    queue = [(r, c)]
    while queue:
        cr, cc = queue.pop()
        if state[cr][cc] != HIDDEN:
            continue
        state[cr][cc] = REVEALED
        if grid[cr][cc] == 0:
            for dr in range(-1, 2):
                for dc in range(-1, 2):
                    nr, nc = cr + dr, cc + dc
                    if 0 <= nr < rows and 0 <= nc < cols and state[nr][nc] == HIDDEN:
                        queue.append((nr, nc))


def check_win(grid, state, rows, cols):
    return all(state[r][c] == REVEALED
               for r in range(rows) for c in range(cols) if grid[r][c] != -1)


class Game:
    def __init__(self, difficulty="easy"):
        self.difficulty = difficulty
        self._reset()

    def _reset(self):
        self.rows, self.cols, self.mines = DIFFICULTIES[self.difficulty]
        self.grid = None
        self.state = [[HIDDEN] * self.cols for _ in range(self.rows)]
        self.cursor_r, self.cursor_c = self.rows // 2, self.cols // 2
        self.started = self.over = self.won = False
        self.start_time = None
        self.elapsed = 0

    def restart(self):
        self._reset()

    def set_difficulty(self, d):
        if d in DIFFICULTIES:
            self.difficulty = d
            self._reset()

    def flag_count(self):
        return sum(1 for row in self.state for s in row if s == FLAGGED)

    def reveal(self):
        r, c = self.cursor_r, self.cursor_c
        if self.state[r][c] != HIDDEN:
            return
        if not self.started:
            self.started = True
            self.start_time = time.time()
            self.grid, _ = make_board(self.rows, self.cols, self.mines, r, c)
        if self.grid[r][c] == -1:
            self.state[r][c] = REVEALED
            self.over = True
        else:
            flood_reveal(self.grid, self.state, self.rows, self.cols, r, c)
            if check_win(self.grid, self.state, self.rows, self.cols):
                self.won = self.over = True

    def toggle_flag(self):
        r, c = self.cursor_r, self.cursor_c
        if self.state[r][c] == HIDDEN:
            self.state[r][c] = FLAGGED
        elif self.state[r][c] == FLAGGED:
            self.state[r][c] = HIDDEN

    def move(self, dr, dc):
        self.cursor_r = max(0, min(self.rows - 1, self.cursor_r + dr))
        self.cursor_c = max(0, min(self.cols - 1, self.cursor_c + dc))

    def tick(self):
        if self.started and not self.over:
            self.elapsed = int(time.time() - self.start_time)


def _cell(game, r, c):
    is_cursor = (r == game.cursor_r and c == game.cursor_c)
    s = game.state[r][c]
    if game.over and game.grid and game.grid[r][c] == -1:
        text, attr = (" F ", curses.color_pair(P_FLAG) | curses.A_BOLD) if s == FLAGGED \
            else (" * ", curses.color_pair(P_MINE) | curses.A_BOLD)
        if is_cursor:
            attr = curses.color_pair(P_CURSOR_H) | curses.A_BOLD
    elif s == FLAGGED:
        text, attr = " F ", curses.color_pair(P_FLAG) | curses.A_BOLD
        if is_cursor:
            attr = curses.color_pair(P_CURSOR_F) | curses.A_BOLD
    elif s == HIDDEN:
        text, attr = "   ", curses.color_pair(P_HIDDEN)
        if is_cursor:
            attr = curses.color_pair(P_CURSOR_H) | curses.A_BOLD
    else:
        val = game.grid[r][c] if game.grid else 0
        text, attr = (f" {val} ", curses.color_pair(val) | curses.A_BOLD) if val > 0 \
            else ("   ", curses.color_pair(P_EMPTY))
        if is_cursor:
            attr = curses.color_pair(P_CURSOR_R) | curses.A_BOLD
    return text, attr


def _draw(stdscr, game, theme):
    stdscr.erase()
    max_y, max_x = stdscr.getmaxyx()
    remaining = game.mines - game.flag_count()
    header = (f"  MINESWEEPER   Mines {remaining:3d}   Time {game.elapsed:4d}s   "
              f"{game.difficulty.upper():6s}   Theme: {theme}  ")
    try:
        stdscr.addstr(0, 0, header[:max_x - 1].ljust(max_x - 1),
                      curses.color_pair(themes.HEADER) | curses.A_BOLD)
    except curses.error:
        pass

    by, bx, cw = 2, 2, 3
    for r in range(game.rows):
        for c in range(game.cols):
            y, x = by + r, bx + c * cw
            if y >= max_y or x + cw > max_x:
                continue
            text, attr = _cell(game, r, c)
            try:
                stdscr.addstr(y, x, text, attr)
            except curses.error:
                pass

    sy = by + game.rows + 1
    if sy < max_y:
        if game.over and game.won:
            msg, attr = f"  Cleared in {game.elapsed}s!  R restart   M menu   Q quit  ", \
                curses.color_pair(P_WIN) | curses.A_BOLD
        elif game.over:
            msg, attr = "  BOOM! You hit a mine.  R restart   M menu   Q quit  ", \
                curses.color_pair(P_LOSE) | curses.A_BOLD
        else:
            msg, attr = ("  Move WASD/arrows  Reveal space  Flag F  1/2/3 difficulty  "
                         "T theme  R restart  M menu  Q quit  "), \
                curses.color_pair(themes.BG) | curses.A_BOLD
        try:
            stdscr.addstr(sy, 0, msg[:max_x - 1], attr)
        except curses.error:
            pass
    stdscr.refresh()


def run(stdscr, theme):
    """Play Minesweeper until the player quits to the menu. Returns the theme."""
    apply_theme(stdscr, theme)
    stdscr.nodelay(True)
    stdscr.timeout(200)
    game = Game("easy")

    while True:
        game.tick()
        _draw(stdscr, game, theme)
        key = stdscr.getch()
        if key == -1:
            continue
        if key in (ord("q"), ord("Q"), ord("m"), ord("M")):
            return theme
        if key in (ord("r"), ord("R")):
            game.restart(); continue
        if key in (ord("t"), ord("T")):
            theme = themes.pick(stdscr, theme)
            apply_theme(stdscr, theme)
            stdscr.nodelay(True); stdscr.timeout(200)
            continue
        if key == ord("1"):
            game.set_difficulty("easy"); continue
        if key == ord("2"):
            game.set_difficulty("medium"); continue
        if key == ord("3"):
            game.set_difficulty("hard"); continue
        if game.over:
            continue
        if key in (curses.KEY_UP, ord("w"), ord("W")):
            game.move(-1, 0)
        elif key in (curses.KEY_DOWN, ord("s"), ord("S")):
            game.move(1, 0)
        elif key in (curses.KEY_LEFT, ord("a"), ord("A")):
            game.move(0, -1)
        elif key in (curses.KEY_RIGHT, ord("d"), ord("D")):
            game.move(0, 1)
        elif key in (ord(" "), ord("\n"), curses.KEY_ENTER):
            game.reveal()
        elif key in (ord("f"), ord("F")):
            game.toggle_flag()
