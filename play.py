#!/usr/bin/env python3
"""Terminal Games launcher.

Run with `python3 play.py`. Pick a game from the menu, play it, and press M
(or Q) inside a game to return here. Themes are shared across every game and
can be changed from the menu or from inside any game with T.
"""

import curses

from common import themes
from games import minesweeper, game_2048

GAMES = [minesweeper, game_2048]


def _draw_menu(stdscr, items, sel, theme):
    stdscr.erase()
    max_y, max_x = stdscr.getmaxyx()

    def put(y, x, text, attr=0):
        if 0 <= y < max_y and 0 <= x < max_x:
            try:
                stdscr.addstr(y, x, text[:max_x - x - 1], attr)
            except curses.error:
                pass

    put(1, 2, "  TERMINAL GAMES  ", curses.color_pair(themes.HEADER) | curses.A_BOLD)
    put(3, 2, "Choose a game:", curses.color_pair(themes.BG) | curses.A_BOLD)

    for i, (label, desc) in enumerate(items):
        y = 5 + i * 2
        marker = " > " if i == sel else "   "
        attr = (curses.color_pair(themes.HILITE) | curses.A_BOLD) if i == sel \
            else (curses.color_pair(themes.BG) | curses.A_BOLD)
        put(y, 2, (marker + label).ljust(22), attr)
        put(y, 26, desc, curses.color_pair(themes.BG))

    put(5 + len(items) * 2 + 1, 2, f"Theme: {theme}",
        curses.color_pair(themes.BG) | curses.A_BOLD)
    put(5 + len(items) * 2 + 3, 2, "Up/Down move    Enter select    Q quit",
        curses.color_pair(themes.BG) | curses.A_BOLD)
    stdscr.refresh()


def main(stdscr):
    curses.curs_set(0)
    themes.init()
    theme = themes.default()

    items = [(g.NAME, g.DESC) for g in GAMES]
    items.append(("Change Theme", "Pick a color scheme for every game."))
    items.append(("Quit", "Exit to the terminal."))

    sel = 0
    stdscr.nodelay(False)
    while True:
        themes.apply_chrome(stdscr, theme)
        _draw_menu(stdscr, items, sel, theme)
        key = stdscr.getch()

        if key in (curses.KEY_UP, ord("w"), ord("W"), ord("k")):
            sel = (sel - 1) % len(items)
        elif key in (curses.KEY_DOWN, ord("s"), ord("S"), ord("j")):
            sel = (sel + 1) % len(items)
        elif key in (ord("q"), ord("Q")):
            break
        elif key in (ord("\n"), curses.KEY_ENTER, ord(" ")):
            if sel < len(GAMES):
                theme = GAMES[sel].run(stdscr, theme)
                stdscr.nodelay(False)
            elif items[sel][0] == "Change Theme":
                theme = themes.pick(stdscr, theme)
                stdscr.nodelay(False)
            else:  # Quit
                break


if __name__ == "__main__":
    curses.wrapper(main)
