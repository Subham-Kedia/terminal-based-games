"""Shared color-theme engine for the terminal games collection.

A theme is a generic *palette* — a background, a raised "surface", muted/foreground
text colors, eight distinct accent colors, and a few semantic shortcuts
(red/green/yellow). Each game maps these palette entries onto its own curses
color pairs, so the same seven popular schemes work everywhere.

Capability is detected once: truecolor (exact RGB), 256-color (nearest match),
or basic (only the ANSI "Classic" theme survives).

Reserved curses color-pair numbers (games must avoid these):
  198 = HILITE   selection highlight (bg on accent)
  199 = HEADER   header bar          (bg on accent)
  200 = BG       screen background   (fg on bg)
  201..213       theme-picker swatches
Games are free to use pairs 1..50.
"""

import curses

HILITE = 198
HEADER = 199
BG = 200
_SWATCH = 201  # 201..213 reserved for the picker

# ---------------------------------------------------------------------------
# Palettes. Accents are eight visually distinct colors (low->high "heat").
# Classic uses ANSI color *integers* and is the universal fallback.
# ---------------------------------------------------------------------------
_C = curses  # short alias for the ANSI constants below
THEMES = {
    "Classic": {
        "ansi": True,
        "note": "The original ANSI palette — works on any terminal.",
        "bg": -1, "surface": _C.COLOR_BLACK, "dim": _C.COLOR_WHITE, "fg": _C.COLOR_WHITE,
        "accents": [_C.COLOR_CYAN, _C.COLOR_GREEN, _C.COLOR_RED, _C.COLOR_MAGENTA,
                    _C.COLOR_YELLOW, _C.COLOR_BLUE, _C.COLOR_WHITE, _C.COLOR_MAGENTA],
        "red": _C.COLOR_RED, "green": _C.COLOR_GREEN, "yellow": _C.COLOR_YELLOW,
    },
    "Dracula": {
        "note": "Moody purple night — punchy accents, very easy to scan.",
        "bg": "#282a36", "surface": "#44475a", "dim": "#6272a4", "fg": "#f8f8f2",
        "accents": ["#8be9fd", "#50fa7b", "#ff5555", "#bd93f9",
                    "#ff79c6", "#ffb86c", "#f1fa8c", "#f8f8f2"],
        "red": "#ff5555", "green": "#50fa7b", "yellow": "#f1fa8c",
    },
    "Nord": {
        "note": "Cool arctic frost — low contrast, calm on the eyes.",
        "bg": "#2e3440", "surface": "#3b4252", "dim": "#4c566a", "fg": "#d8dee9",
        "accents": ["#81a1c1", "#a3be8c", "#bf616a", "#b48ead",
                    "#d08770", "#88c0d0", "#e5e9f0", "#8fbcbb"],
        "red": "#bf616a", "green": "#a3be8c", "yellow": "#ebcb8b",
    },
    "Gruvbox": {
        "note": "Warm retro earth tones — cozy and highly readable.",
        "bg": "#282828", "surface": "#3c3836", "dim": "#928374", "fg": "#ebdbb2",
        "accents": ["#83a598", "#b8bb26", "#fb4934", "#d3869b",
                    "#fe8019", "#8ec07c", "#ebdbb2", "#fabd2f"],
        "red": "#fb4934", "green": "#b8bb26", "yellow": "#fabd2f",
    },
    "Solarized Dark": {
        "note": "Precision-balanced palette — gentle and scientific.",
        "bg": "#002b36", "surface": "#073642", "dim": "#586e75", "fg": "#839496",
        "accents": ["#268bd2", "#859900", "#dc322f", "#6c71c4",
                    "#cb4b16", "#2aa198", "#93a1a1", "#d33682"],
        "red": "#dc322f", "green": "#859900", "yellow": "#b58900",
    },
    "Monokai": {
        "note": "Vivid and high-energy — bold neon accents.",
        "bg": "#272822", "surface": "#3e3d32", "dim": "#75715e", "fg": "#f8f8f2",
        "accents": ["#66d9ef", "#a6e22e", "#f92672", "#ae81ff",
                    "#fd971f", "#e6db74", "#f8f8f2", "#75715e"],
        "red": "#f92672", "green": "#a6e22e", "yellow": "#e6db74",
    },
    "Tokyo Night": {
        "note": "Deep blue neon — sleek, modern, midnight dark.",
        "bg": "#1a1b26", "surface": "#292e42", "dim": "#565f89", "fg": "#c0caf5",
        "accents": ["#7aa2f7", "#9ece6a", "#f7768e", "#bb9af7",
                    "#ff9e64", "#7dcfff", "#c0caf5", "#e0af68"],
        "red": "#f7768e", "green": "#9ece6a", "yellow": "#e0af68",
    },
}
THEME_ORDER = ["Classic", "Dracula", "Nord", "Gruvbox",
               "Solarized Dark", "Monokai", "Tokyo Night"]

_MODE = "basic"          # "truecolor" | "256" | "basic"
_slot = [16]             # next free custom-color slot (truecolor mode)
_cache = {}              # hex -> curses color number (persists for the session)


def init():
    """Start curses colors, detect capability, and trim the menu if needed."""
    global _MODE, THEME_ORDER
    curses.start_color()
    curses.use_default_colors()
    if curses.can_change_color() and curses.COLORS >= 32:
        _MODE = "truecolor"
    elif curses.COLORS >= 256:
        _MODE = "256"
    else:
        _MODE = "basic"
        THEME_ORDER = ["Classic"]


def default():
    return "Dracula" if "Dracula" in THEME_ORDER else "Classic"


def palette(name):
    return THEMES[name]


def _hex_to_1000(h):
    h = h.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return r * 1000 // 255, g * 1000 // 255, b * 1000 // 255


def _nearest_256(h):
    h = h.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    if abs(r - g) < 10 and abs(g - b) < 10:           # grayscale ramp
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


def color(value):
    """Resolve a palette value (hex string or ANSI int) to a curses color number."""
    if isinstance(value, int):       # ANSI constant or -1 (default)
        return value
    if value in _cache:
        return _cache[value]
    if _MODE == "truecolor":
        idx = _slot[0]
        _slot[0] += 1
        try:
            curses.init_color(idx, *_hex_to_1000(value))
        except curses.error:
            idx = _nearest_256(value)
    else:
        idx = _nearest_256(value)
    _cache[value] = idx
    return idx


def apply_chrome(stdscr, name):
    """Set the shared chrome pairs (BG / HEADER / HILITE) and tint the screen."""
    p = THEMES[name]
    curses.init_pair(BG,     color(p["fg"]),  color(p["bg"]))
    curses.init_pair(HEADER, color(p["bg"]),  color(p["accents"][3]))
    curses.init_pair(HILITE, color(p["bg"]),  color(p["accents"][5]))
    stdscr.bkgd(" ", curses.color_pair(BG))


# ---------------------------------------------------------------------------
# Theme picker overlay (live preview, game-agnostic)
# ---------------------------------------------------------------------------
def _draw_picker(stdscr, idx):
    stdscr.erase()
    max_y, max_x = stdscr.getmaxyx()
    name = THEME_ORDER[idx]
    p = THEMES[name]

    def put(y, x, text, attr=0):
        if 0 <= y < max_y and 0 <= x < max_x:
            try:
                stdscr.addstr(y, x, text[:max_x - x - 1], attr)
            except curses.error:
                pass

    put(1, 2, "  CHOOSE A COLOR THEME  ", curses.color_pair(HEADER) | curses.A_BOLD)
    top = 3
    for i, n in enumerate(THEME_ORDER):
        marker = " > " if i == idx else "   "
        attr = (curses.color_pair(HILITE) | curses.A_BOLD) if i == idx \
            else (curses.color_pair(BG) | curses.A_BOLD)
        put(top + i, 2, (marker + n).ljust(20), attr)

    py = top + len(THEME_ORDER) + 1
    put(py, 2, "Swatches:", curses.color_pair(BG) | curses.A_BOLD)
    px = 12
    for i in range(len(p["accents"])):
        put(py, px, "  ", curses.color_pair(_SWATCH + i))
        px += 2
    put(py + 1, 2, p.get("note", ""), curses.color_pair(BG))
    put(py + 3, 2, "Up/Down browse    Enter select    Esc cancel",
        curses.color_pair(BG) | curses.A_BOLD)
    stdscr.refresh()


def pick(stdscr, current):
    """Blocking overlay; live-applies each theme as you browse. Returns a name.

    Leaves the terminal in blocking-input mode; callers that need a timeout
    (real-time games) should restore it after this returns.
    """
    idx = THEME_ORDER.index(current) if current in THEME_ORDER else 0
    stdscr.nodelay(False)
    chosen = current
    while True:
        name = THEME_ORDER[idx]
        p = THEMES[name]
        apply_chrome(stdscr, name)
        for i, accent in enumerate(p["accents"]):
            curses.init_pair(_SWATCH + i, color(p["bg"]), color(accent))
        _draw_picker(stdscr, idx)

        k = stdscr.getch()
        if k in (curses.KEY_UP, ord("w"), ord("W"), ord("k")):
            idx = (idx - 1) % len(THEME_ORDER)
        elif k in (curses.KEY_DOWN, ord("s"), ord("S"), ord("j")):
            idx = (idx + 1) % len(THEME_ORDER)
        elif k in (ord("\n"), curses.KEY_ENTER, ord(" ")):
            chosen = name
            break
        elif k in (27, ord("q"), ord("Q")):
            chosen = current
            apply_chrome(stdscr, current)
            break
    return chosen
