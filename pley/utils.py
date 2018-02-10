import time
import curses
import pprint


def debug(msg, pretty=False, slp=None):
    if not debug.win:
        debug.win = curses.newwin(curses.LINES-10, curses.COLS-4, 5, 2)
        debug.win.idlok(True)
        debug.win.scrollok(True)
    if pretty:
        debug.win.move(0, 0)
        debug.win.clear()
        debug.y = 1
        debug.win.addstr(debug.y, 2, pprint.pformat(msg))
    else:
        debug.win.addstr(debug.y, 2, msg)
    debug.win.border()
    debug.win.refresh()
    debug.y += 1
    if slp:
        time.sleep(slp)
debug.win = None
debug.y = 1
