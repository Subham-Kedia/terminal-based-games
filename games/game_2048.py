"""2048 — slide and merge tiles to reach 2048 (and beyond).

Exposes run(stdscr, theme) for the launcher. Returns the (possibly changed)
theme name. Turn-based, so it uses blocking input.
"""

import curses
import random

from common import themes

NAME = "2048"
DESC = "Slide tiles to merge matching numbers up to 2048."

SIZE = 4
TARGET = 2048

# Game-local color pairs.
P_RAMP = 1     # tile colors live in pairs 1..11 (by exponent)
RAMP_LEN = 11
P_EMPTY, P_WIN, P_LOSE = 12, 13, 14


def apply_theme(stdscr, name):
    p = themes.palette(name)
    c = themes.color
    a = p["accents"]
    # Cool -> warm progression for ascending tile values.
    ramp = [a[0], a[5], a[1], a[6], a[4], a[2], a[3], a[7],
            p["green"], p["red"], p["yellow"]]
    for i, col in enumerate(ramp):
        curses.init_pair(P_RAMP + i, c(p["bg"]), c(col))     # dark text on bright tile
    curses.init_pair(P_EMPTY, c(p["dim"]), c(p["surface"]))
    curses.init_pair(P_WIN,   c(p["bg"]),  c(p["green"]))
    curses.init_pair(P_LOSE,  c(p["fg"]),  c(p["red"]))
    themes.apply_chrome(stdscr, name)


def _tile_pair(value):
    exp = value.bit_length() - 1            # 2->1, 4->2, 8->3, ...
    return P_RAMP + (exp - 1) % RAMP_LEN


# --------------------------------------------------------------------------
# Pure game logic
# --------------------------------------------------------------------------
def new_grid():
    g = [[0] * SIZE for _ in range(SIZE)]
    spawn(g)
    spawn(g)
    return g


def spawn(grid):
    empty = [(r, c) for r in range(SIZE) for c in range(SIZE) if grid[r][c] == 0]
    if not empty:
        return False
    r, c = random.choice(empty)
    grid[r][c] = 4 if random.random() < 0.1 else 2
    return True


def _merge_left(row):
    """Slide non-zeros left and merge equal neighbors once. Returns (row, gained)."""
    nums = [x for x in row if x]
    out, gained, i = [], 0, 0
    while i < len(nums):
        if i + 1 < len(nums) and nums[i] == nums[i + 1]:
            out.append(nums[i] * 2)
            gained += nums[i] * 2
            i += 2
        else:
            out.append(nums[i])
            i += 1
    out += [0] * (SIZE - len(out))
    return out, gained


def _reverse(g):
    return [row[::-1] for row in g]


def _transpose(g):
    return [list(col) for col in zip(*g)]


def apply_move(grid, direction):
    """Return (new_grid, moved, gained) for 'left'/'right'/'up'/'down'."""
    if direction == "left":
        work = grid
    elif direction == "right":
        work = _reverse(grid)
    elif direction == "up":
        work = _transpose(grid)
    elif direction == "down":
        work = _reverse(_transpose(grid))
    else:
        return grid, False, 0

    merged, gained = [], 0
    for row in work:
        new_row, sc = _merge_left(row)
        merged.append(new_row)
        gained += sc

    if direction == "right":
        merged = _reverse(merged)
    elif direction == "up":
        merged = _transpose(merged)
    elif direction == "down":
        merged = _transpose(_reverse(merged))

    moved = merged != grid
    return merged, moved, gained


def can_move(grid):
    return any(apply_move(grid, d)[1] for d in ("left", "right", "up", "down"))


def has_won(grid):
    return any(v >= TARGET for row in grid for v in row)


class Game:
    def __init__(self):
        self.reset()

    def reset(self):
        self.grid = new_grid()
        self.score = 0
        self.best_tile = 2
        self.over = False
        self.won = False
        self._prev = None        # one-level undo: (grid, score)

    def move(self, direction):
        if self.over:
            return
        new, moved, gained = apply_move(self.grid, direction)
        if not moved:
            return
        self._prev = ([row[:] for row in self.grid], self.score)
        self.grid = new
        self.score += gained
        spawn(self.grid)
        self.best_tile = max(v for row in self.grid for v in row)
        if has_won(self.grid):
            self.won = True
        if not can_move(self.grid):
            self.over = True

    def undo(self):
        if self._prev is not None:
            grid, score = self._prev
            self.grid = [row[:] for row in grid]
            self.score = score
            self._prev = None
            self.over = False


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------
def _draw(stdscr, game, theme):
    stdscr.erase()
    max_y, max_x = stdscr.getmaxyx()
    header = (f"  2048   Score {game.score:6d}   Best {game.best_tile:5d}   "
              f"Theme: {theme}  ")
    try:
        stdscr.addstr(0, 0, header[:max_x - 1].ljust(max_x - 1),
                      curses.color_pair(themes.HEADER) | curses.A_BOLD)
    except curses.error:
        pass

    by, bx, cw, ch = 2, 2, 7, 3          # cell width / height in chars
    for r in range(SIZE):
        for c in range(SIZE):
            v = game.grid[r][c]
            if v:
                attr = curses.color_pair(_tile_pair(v)) | curses.A_BOLD
                label = str(v).center(cw)
            else:
                attr = curses.color_pair(P_EMPTY)
                label = " " * cw
            y0, x0 = by + r * ch, bx + c * cw
            for dy in range(ch):
                text = label if dy == ch // 2 else " " * cw
                yy = y0 + dy
                if yy < max_y and x0 + cw <= max_x:
                    try:
                        stdscr.addstr(yy, x0, text, attr)
                    except curses.error:
                        pass

    sy = by + SIZE * ch + 1
    if sy < max_y:
        if game.over:
            msg, attr = "  No moves left!  R restart   M menu   Q quit  ", \
                curses.color_pair(P_LOSE) | curses.A_BOLD
        elif game.won:
            msg, attr = "  You reached 2048!  Keep going, or R restart   M menu  ", \
                curses.color_pair(P_WIN) | curses.A_BOLD
        else:
            msg, attr = ("  Move WASD/arrows   U undo   T theme   "
                         "R restart   M menu   Q quit  "), \
                curses.color_pair(themes.BG) | curses.A_BOLD
        try:
            stdscr.addstr(sy, 0, msg[:max_x - 1], attr)
        except curses.error:
            pass
    stdscr.refresh()


def run(stdscr, theme):
    """Play 2048 until the player quits to the menu. Returns the theme."""
    apply_theme(stdscr, theme)
    stdscr.nodelay(False)
    game = Game()

    while True:
        _draw(stdscr, game, theme)
        key = stdscr.getch()
        if key in (ord("q"), ord("Q"), ord("m"), ord("M")):
            return theme
        if key in (ord("r"), ord("R")):
            game.reset(); continue
        if key in (ord("u"), ord("U")):
            game.undo(); continue
        if key in (ord("t"), ord("T")):
            theme = themes.pick(stdscr, theme)
            apply_theme(stdscr, theme)
            stdscr.nodelay(False)
            continue
        if key in (curses.KEY_UP, ord("w"), ord("W")):
            game.move("up")
        elif key in (curses.KEY_DOWN, ord("s"), ord("S")):
            game.move("down")
        elif key in (curses.KEY_LEFT, ord("a"), ord("A")):
            game.move("left")
        elif key in (curses.KEY_RIGHT, ord("d"), ord("D")):
            game.move("right")
