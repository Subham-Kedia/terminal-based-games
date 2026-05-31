#!/usr/bin/env python3
"""Terminal Minesweeper with selectable color themes.

Controls:
  Arrows / WASD ...... move cursor
  Space / Enter ...... reveal cell
  F .................. toggle flag
  1 / 2 / 3 .......... easy / medium / hard
  T .................. open theme picker
  R .................. restart
  Q .................. quit
"""

import curses
import random
import time

DIFFICULTIES = {
    "easy":   (9,  9,  10),
    "medium": (16, 16, 40),
    "hard":   (16, 30, 99),
}

HIDDEN, REVEALED, FLAGGED = 0, 1, 2

# ----------------------------------------------------------------------------
# Color pair slots (numbers 1–8 are reserved for the eight count colors)
# ----------------------------------------------------------------------------
C_HIDDEN   = 9
C_FLAG     = 10
C_MINE     = 11
C_CURSOR_H = 12   # cursor on a hidden cell
C_CURSOR_R = 13   # cursor on a revealed cell
C_CURSOR_F = 14   # cursor on a flagged cell
C_EMPTY    = 15   # revealed blank cell
C_HEADER   = 16
C_WIN      = 17
C_LOSE     = 18
C_BG       = 19   # general screen background / status text

# ----------------------------------------------------------------------------
# Themes. Each maps minesweeper roles to hex colors. "num" lists colors for the
# counts 1..8. Classic is special-cased to plain ANSI so it works everywhere.
# The mapping rationale per theme is in the "note" shown by the picker.
# ----------------------------------------------------------------------------
THEMES = {
    "Classic": {
        "ansi": True,
        "note": "The original Windows look — works on any terminal.",
    },
    "Dracula": {
        "note": "Moody purple night — punchy accents, very easy to scan.",
        "board_bg": "#282a36", "hidden_bg": "#44475a", "hidden_fg": "#6272a4",
        "fg": "#f8f8f2",
        "num": ["#8be9fd", "#50fa7b", "#ff5555", "#bd93f9",
                "#ff79c6", "#ffb86c", "#f1fa8c", "#f8f8f2"],
        "flag": "#ff79c6",
        "mine_fg": "#f8f8f2", "mine_bg": "#ff5555",
        "cursor_fg": "#282a36", "cursor_bg": "#f1fa8c",
        "header_fg": "#282a36", "header_bg": "#bd93f9",
        "win_fg": "#282a36", "win_bg": "#50fa7b",
        "lose_fg": "#f8f8f2", "lose_bg": "#ff5555",
    },
    "Nord": {
        "note": "Cool arctic frost — low contrast, calm on the eyes.",
        "board_bg": "#2e3440", "hidden_bg": "#3b4252", "hidden_fg": "#4c566a",
        "fg": "#d8dee9",
        "num": ["#81a1c1", "#a3be8c", "#bf616a", "#b48ead",
                "#d08770", "#88c0d0", "#e5e9f0", "#8fbcbb"],
        "flag": "#ebcb8b",
        "mine_fg": "#eceff4", "mine_bg": "#bf616a",
        "cursor_fg": "#2e3440", "cursor_bg": "#88c0d0",
        "header_fg": "#2e3440", "header_bg": "#81a1c1",
        "win_fg": "#2e3440", "win_bg": "#a3be8c",
        "lose_fg": "#eceff4", "lose_bg": "#bf616a",
    },
    "Gruvbox": {
        "note": "Warm retro earth tones — cozy and highly readable.",
        "board_bg": "#282828", "hidden_bg": "#3c3836", "hidden_fg": "#928374",
        "fg": "#ebdbb2",
        "num": ["#83a598", "#b8bb26", "#fb4934", "#d3869b",
                "#fe8019", "#8ec07c", "#ebdbb2", "#fabd2f"],
        "flag": "#fabd2f",
        "mine_fg": "#fbf1c7", "mine_bg": "#cc241d",
        "cursor_fg": "#282828", "cursor_bg": "#fabd2f",
        "header_fg": "#282828", "header_bg": "#fe8019",
        "win_fg": "#282828", "win_bg": "#b8bb26",
        "lose_fg": "#fbf1c7", "lose_bg": "#cc241d",
    },
    "Solarized Dark": {
        "note": "Precision-balanced palette — gentle and scientific.",
        "board_bg": "#002b36", "hidden_bg": "#073642", "hidden_fg": "#586e75",
        "fg": "#839496",
        "num": ["#268bd2", "#859900", "#dc322f", "#6c71c4",
                "#cb4b16", "#2aa198", "#93a1a1", "#d33682"],
        "flag": "#b58900",
        "mine_fg": "#fdf6e3", "mine_bg": "#dc322f",
        "cursor_fg": "#002b36", "cursor_bg": "#2aa198",
        "header_fg": "#002b36", "header_bg": "#268bd2",
        "win_fg": "#002b36", "win_bg": "#859900",
        "lose_fg": "#fdf6e3", "lose_bg": "#dc322f",
    },
    "Monokai": {
        "note": "Vivid and high-energy — bold neon accents.",
        "board_bg": "#272822", "hidden_bg": "#3e3d32", "hidden_fg": "#75715e",
        "fg": "#f8f8f2",
        "num": ["#66d9ef", "#a6e22e", "#f92672", "#ae81ff",
                "#fd971f", "#e6db74", "#f8f8f2", "#75715e"],
        "flag": "#fd971f",
        "mine_fg": "#f8f8f2", "mine_bg": "#f92672",
        "cursor_fg": "#272822", "cursor_bg": "#e6db74",
        "header_fg": "#272822", "header_bg": "#a6e22e",
        "win_fg": "#272822", "win_bg": "#a6e22e",
        "lose_fg": "#f8f8f2", "lose_bg": "#f92672",
    },
    "Tokyo Night": {
        "note": "Deep blue neon — sleek, modern, midnight dark.",
        "board_bg": "#1a1b26", "hidden_bg": "#292e42", "hidden_fg": "#565f89",
        "fg": "#c0caf5",
        "num": ["#7aa2f7", "#9ece6a", "#f7768e", "#bb9af7",
                "#ff9e64", "#7dcfff", "#c0caf5", "#e0af68"],
        "flag": "#e0af68",
        "mine_fg": "#c0caf5", "mine_bg": "#f7768e",
        "cursor_fg": "#1a1b26", "cursor_bg": "#7dcfff",
        "header_fg": "#1a1b26", "header_bg": "#7aa2f7",
        "win_fg": "#1a1b26", "win_bg": "#9ece6a",
        "lose_fg": "#c0caf5", "lose_bg": "#f7768e",
    },
}
THEME_ORDER = ["Classic", "Dracula", "Nord", "Gruvbox",
               "Solarized Dark", "Monokai", "Tokyo Night"]

# Filled in by setup_color_mode(): "truecolor", "256", or "basic".
COLOR_MODE = "basic"
_color_slot = [16]
_color_cache = {}


def setup_color_mode():
    """Decide how rich we can be, and trim the theme menu accordingly."""
    global COLOR_MODE, THEME_ORDER
    curses.start_color()
    curses.use_default_colors()
    if curses.can_change_color() and curses.COLORS >= 32:
        COLOR_MODE = "truecolor"
    elif curses.COLORS >= 256:
        COLOR_MODE = "256"
    else:
        COLOR_MODE = "basic"
        THEME_ORDER = ["Classic"]


def _hex_to_1000(h):
    h = h.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return r * 1000 // 255, g * 1000 // 255, b * 1000 // 255


def _nearest_256(h):
    """Map a hex color to the closest xterm-256 cube/grayscale index."""
    h = h.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    if abs(r - g) < 10 and abs(g - b) < 10:  # grayscale ramp 232..255
        gray = (r + g + b) // 3
        if gray < 8:
            return 16
        if gray > 248:
            return 231
        return 232 + (gray - 8) * 24 // 247

    def cube(v):
        if v < 48:
            return 0
        if v < 115:
            return 1
        return min(5, (v - 35) // 40)

    return 16 + 36 * cube(r) + 6 * cube(g) + cube(b)


def _color(h):
    """Return a usable curses color number for a hex string."""
    if h in _color_cache:
        return _color_cache[h]
    if COLOR_MODE == "truecolor":
        idx = _color_slot[0]
        _color_slot[0] += 1
        try:
            curses.init_color(idx, *_hex_to_1000(h))
        except curses.error:
            idx = _nearest_256(h)
    else:  # "256"
        idx = _nearest_256(h)
    _color_cache[h] = idx
    return idx


def _apply_classic():
    """Plain ANSI theme — the universal fallback, always available."""
    pairs = {
        1: (curses.COLOR_CYAN, -1), 2: (curses.COLOR_GREEN, -1),
        3: (curses.COLOR_RED, -1), 4: (curses.COLOR_MAGENTA, -1),
        5: (curses.COLOR_RED, -1), 6: (curses.COLOR_CYAN, -1),
        7: (curses.COLOR_WHITE, -1), 8: (curses.COLOR_WHITE, -1),
        C_HIDDEN:   (curses.COLOR_WHITE, curses.COLOR_BLACK),
        C_FLAG:     (curses.COLOR_YELLOW, curses.COLOR_BLACK),
        C_MINE:     (curses.COLOR_WHITE, curses.COLOR_RED),
        C_CURSOR_H: (curses.COLOR_BLACK, curses.COLOR_WHITE),
        C_CURSOR_R: (curses.COLOR_BLACK, curses.COLOR_WHITE),
        C_CURSOR_F: (curses.COLOR_YELLOW, curses.COLOR_WHITE),
        C_EMPTY:    (-1, -1),
        C_HEADER:   (curses.COLOR_BLACK, curses.COLOR_CYAN),
        C_WIN:      (curses.COLOR_BLACK, curses.COLOR_GREEN),
        C_LOSE:     (curses.COLOR_YELLOW, curses.COLOR_RED),
        C_BG:       (-1, -1),
    }
    for idx, (fg, bg) in pairs.items():
        curses.init_pair(idx, fg, bg)


def apply_theme(stdscr, name):
    """Configure all color pairs for the given theme and tint the screen."""
    t = THEMES[name]
    if t.get("ansi") or COLOR_MODE == "basic":
        _apply_classic()
        stdscr.bkgd(" ", curses.color_pair(0))
        return

    _color_cache.clear()
    _color_slot[0] = 16

    bg = _color(t["board_bg"])
    for i in range(1, 9):
        curses.init_pair(i, _color(t["num"][i - 1]), bg)
    curses.init_pair(C_HIDDEN,   _color(t["hidden_fg"]), _color(t["hidden_bg"]))
    curses.init_pair(C_FLAG,     _color(t["flag"]),      _color(t["hidden_bg"]))
    curses.init_pair(C_MINE,     _color(t["mine_fg"]),   _color(t["mine_bg"]))
    curses.init_pair(C_CURSOR_H, _color(t["cursor_fg"]), _color(t["cursor_bg"]))
    curses.init_pair(C_CURSOR_R, _color(t["cursor_fg"]), _color(t["cursor_bg"]))
    curses.init_pair(C_CURSOR_F, _color(t["flag"]),      _color(t["cursor_bg"]))
    curses.init_pair(C_EMPTY,    bg, bg)
    curses.init_pair(C_HEADER,   _color(t["header_fg"]), _color(t["header_bg"]))
    curses.init_pair(C_WIN,      _color(t["win_fg"]),    _color(t["win_bg"]))
    curses.init_pair(C_LOSE,     _color(t["lose_fg"]),   _color(t["lose_bg"]))
    curses.init_pair(C_BG,       _color(t["fg"]),        bg)
    stdscr.bkgd(" ", curses.color_pair(C_BG))


# ----------------------------------------------------------------------------
# Game logic
# ----------------------------------------------------------------------------
def make_board(rows, cols, mines, safe_r, safe_c):
    """Build the mine grid after the first reveal so the first click is safe."""
    safe = {
        (safe_r + dr, safe_c + dc)
        for dr in range(-1, 2) for dc in range(-1, 2)
        if 0 <= safe_r + dr < rows and 0 <= safe_c + dc < cols
    }
    candidates = [(r, c) for r in range(rows) for c in range(cols) if (r, c) not in safe]
    mine_set = set(random.sample(candidates, min(mines, len(candidates))))

    grid = [[0] * cols for _ in range(rows)]
    for r, c in mine_set:
        grid[r][c] = -1
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == -1:
                continue
            grid[r][c] = sum(
                1 for dr in range(-1, 2) for dc in range(-1, 2)
                if 0 <= r + dr < rows and 0 <= c + dc < cols and grid[r + dr][c + dc] == -1
            )
    return grid, mine_set


def flood_reveal(grid, state, rows, cols, r, c):
    """Reveal connected empty cells via BFS."""
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
    return all(
        state[r][c] == REVEALED
        for r in range(rows) for c in range(cols)
        if grid[r][c] != -1
    )


class Game:
    def __init__(self, difficulty="easy"):
        self.difficulty = difficulty
        self._reset()

    def _reset(self):
        self.rows, self.cols, self.mines = DIFFICULTIES[self.difficulty]
        self.grid = None
        self.state = [[HIDDEN] * self.cols for _ in range(self.rows)]
        self.mine_set = set()
        self.cursor_r = self.rows // 2
        self.cursor_c = self.cols // 2
        self.started = False
        self.start_time = None
        self.elapsed = 0
        self.over = False
        self.won = False

    def restart(self):
        self._reset()

    def set_difficulty(self, difficulty):
        if difficulty in DIFFICULTIES:
            self.difficulty = difficulty
            self._reset()

    def flag_count(self):
        return sum(
            1 for r in range(self.rows) for c in range(self.cols)
            if self.state[r][c] == FLAGGED
        )

    def reveal(self):
        r, c = self.cursor_r, self.cursor_c
        if self.state[r][c] != HIDDEN:
            return
        if not self.started:
            self.started = True
            self.start_time = time.time()
            self.grid, self.mine_set = make_board(self.rows, self.cols, self.mines, r, c)

        if self.grid[r][c] == -1:
            self.state[r][c] = REVEALED
            self.over = True
        else:
            flood_reveal(self.grid, self.state, self.rows, self.cols, r, c)
            if check_win(self.grid, self.state, self.rows, self.cols):
                self.won = True
                self.over = True

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


# ----------------------------------------------------------------------------
# Rendering
# ----------------------------------------------------------------------------
def cell_render(game, r, c):
    """Return (text, attr) for one board cell."""
    is_cursor = (r == game.cursor_r and c == game.cursor_c)
    s = game.state[r][c]

    if game.over and game.grid and game.grid[r][c] == -1:
        if s == FLAGGED:
            text, attr = " F ", curses.color_pair(C_FLAG) | curses.A_BOLD
        else:
            text, attr = " * ", curses.color_pair(C_MINE) | curses.A_BOLD
        if is_cursor:
            attr = curses.color_pair(C_CURSOR_H) | curses.A_BOLD
    elif s == FLAGGED:
        text, attr = " F ", curses.color_pair(C_FLAG) | curses.A_BOLD
        if is_cursor:
            attr = curses.color_pair(C_CURSOR_F) | curses.A_BOLD
    elif s == HIDDEN:
        text, attr = "   ", curses.color_pair(C_HIDDEN)
        if is_cursor:
            attr = curses.color_pair(C_CURSOR_H) | curses.A_BOLD
    else:  # REVEALED
        val = game.grid[r][c] if game.grid else 0
        if val > 0:
            text, attr = f" {val} ", curses.color_pair(val) | curses.A_BOLD
        else:
            text, attr = "   ", curses.color_pair(C_EMPTY)
        if is_cursor:
            attr = curses.color_pair(C_CURSOR_R) | curses.A_BOLD
    return text, attr


def draw(stdscr, game, theme_name):
    stdscr.erase()
    max_y, max_x = stdscr.getmaxyx()

    remaining = game.mines - game.flag_count()
    header = (
        f"  MINESWEEPER   Mines {remaining:3d}   Time {game.elapsed:4d}s   "
        f"{game.difficulty.upper():6s}   Theme: {theme_name}  "
    )
    try:
        stdscr.addstr(0, 0, header[:max_x - 1].ljust(max_x - 1),
                      curses.color_pair(C_HEADER) | curses.A_BOLD)
    except curses.error:
        pass

    board_y, board_x, cell_w = 2, 2, 3
    for r in range(game.rows):
        for c in range(game.cols):
            y, x = board_y + r, board_x + c * cell_w
            if y >= max_y or x + cell_w > max_x:
                continue
            text, attr = cell_render(game, r, c)
            try:
                stdscr.addstr(y, x, text, attr)
            except curses.error:
                pass

    status_y = board_y + game.rows + 1
    if status_y < max_y:
        if game.over and game.won:
            msg = f"  You cleared the board in {game.elapsed}s!  Press R to play again.  "
            attr = curses.color_pair(C_WIN) | curses.A_BOLD
        elif game.over:
            msg = "  BOOM! You hit a mine.  Press R to restart.  "
            attr = curses.color_pair(C_LOSE) | curses.A_BOLD
        else:
            msg = "  Move arrows/WASD   Reveal space   Flag F   1/2/3 difficulty   T theme   R restart   Q quit  "
            attr = curses.color_pair(C_BG) | curses.A_BOLD
        try:
            stdscr.addstr(status_y, 0, msg[:max_x - 1], attr)
        except curses.error:
            pass

    stdscr.refresh()


# ----------------------------------------------------------------------------
# Theme picker overlay (live preview)
# ----------------------------------------------------------------------------
def draw_picker(stdscr, idx):
    stdscr.erase()
    max_y, max_x = stdscr.getmaxyx()
    name = THEME_ORDER[idx]

    title = "  CHOOSE A COLOR THEME  "
    try:
        stdscr.addstr(1, 2, title, curses.color_pair(C_HEADER) | curses.A_BOLD)
    except curses.error:
        pass

    top = 3
    for i, n in enumerate(THEME_ORDER):
        marker = ">" if i == idx else " "
        line = f" {marker} {n} "
        attr = (curses.color_pair(C_HEADER) | curses.A_BOLD) if i == idx \
            else (curses.color_pair(C_BG) | curses.A_BOLD)
        try:
            stdscr.addstr(top + i, 2, line.ljust(20), attr)
        except curses.error:
            pass

    # Live preview swatch for the highlighted theme (colors are already applied)
    py = top + len(THEME_ORDER) + 1
    try:
        stdscr.addstr(py, 2, "Preview:", curses.color_pair(C_BG) | curses.A_BOLD)
        px = 12
        for i in range(1, 9):
            stdscr.addstr(py, px, f" {i} ", curses.color_pair(i) | curses.A_BOLD)
            px += 3
        stdscr.addstr(py, px + 1, " F ", curses.color_pair(C_FLAG) | curses.A_BOLD)
        stdscr.addstr(py, px + 4, " * ", curses.color_pair(C_MINE) | curses.A_BOLD)
        stdscr.addstr(py, px + 7, "   ", curses.color_pair(C_HIDDEN))
        stdscr.addstr(py, px + 10, "   ", curses.color_pair(C_EMPTY))

        note = THEMES[name].get("note", "")
        stdscr.addstr(py + 2, 2, note[:max_x - 4], curses.color_pair(C_BG))
        stdscr.addstr(py + 4, 2, "Up/Down to browse   Enter to select   Esc to cancel",
                      curses.color_pair(C_BG) | curses.A_BOLD)
    except curses.error:
        pass

    stdscr.refresh()


def theme_picker(stdscr, current):
    """Blocking overlay; live-applies themes as you browse. Returns chosen name."""
    idx = THEME_ORDER.index(current) if current in THEME_ORDER else 0
    stdscr.nodelay(False)
    chosen = current
    while True:
        apply_theme(stdscr, THEME_ORDER[idx])
        draw_picker(stdscr, idx)
        k = stdscr.getch()
        if k in (curses.KEY_UP, ord("w"), ord("W"), ord("k")):
            idx = (idx - 1) % len(THEME_ORDER)
        elif k in (curses.KEY_DOWN, ord("s"), ord("S"), ord("j")):
            idx = (idx + 1) % len(THEME_ORDER)
        elif k in (ord("\n"), curses.KEY_ENTER, ord(" ")):
            chosen = THEME_ORDER[idx]
            break
        elif k in (27, ord("q"), ord("Q")):
            chosen = current
            apply_theme(stdscr, current)
            break
    stdscr.nodelay(True)
    stdscr.timeout(200)
    return chosen


# ----------------------------------------------------------------------------
# Main loop
# ----------------------------------------------------------------------------
def main(stdscr):
    curses.curs_set(0)
    setup_color_mode()

    theme = "Dracula" if "Dracula" in THEME_ORDER else "Classic"
    apply_theme(stdscr, theme)

    # Let the player pick a theme up front.
    theme = theme_picker(stdscr, theme)

    stdscr.nodelay(True)
    stdscr.timeout(200)
    game = Game("easy")

    while True:
        game.tick()
        draw(stdscr, game, theme)

        key = stdscr.getch()
        if key == -1:
            continue
        if key in (ord("q"), ord("Q")):
            break
        if key in (ord("r"), ord("R")):
            game.restart()
            continue
        if key in (ord("t"), ord("T")):
            theme = theme_picker(stdscr, theme)
            continue
        if key == ord("1"):
            game.set_difficulty("easy");   continue
        if key == ord("2"):
            game.set_difficulty("medium"); continue
        if key == ord("3"):
            game.set_difficulty("hard");   continue

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


if __name__ == "__main__":
    curses.wrapper(main)
