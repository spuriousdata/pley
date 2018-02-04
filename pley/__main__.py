#!/usr/bin/env python3

import curses
from pley.api import Plex
from pley.display import UI
from pley import config


def main(stdscr):
    config.init()
    plex = Plex(config.get('host'), config.get('token'))
    # supports only music for now
    plex.filter(type='artist')
    ui = UI(stdscr, plex)
    ui.loop()


def _main():
    curses.wrapper(main)


if __name__ == '__main__':
    _main()
