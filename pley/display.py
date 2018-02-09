import curses
from collections import namedtuple
from pley.utils import debug
from pley.player import Player


class Callback(object):
    def __init__(self, action, args, kwargs):
        self.action = action
        self.args = args
        self.kwargs = kwargs

    def __call__(self):
        self.action(*self.args, **self.kwargs)


class UI(object):
    def __init__(self, stdscr, plex):
        self.callbacks = {}
        curses.curs_set(0)
        self.win = stdscr
        self.win.clear()
        self.win.addstr(("{:^%d}" % curses.COLS).format(" Pley: PLEx plaYer "))
        self.main = MainPanel(self, curses.LINES - 4, 1, plex)
        self.player = Player(PlayerPanel(self), plex)
        self.render()

    def render(self):
        self.main.render()
        self.player.render()
        self.win.refresh()

    def play(self, item):
        self.player.play(item)

    def register_callbacks(self, keys, action, *args, **kwargs):
        for key in keys:
            if key in self.callbacks:
                raise Exception("Overwrite of existing callback (%s)" % key)
            self.callbacks[key] = Callback(action, args, kwargs)

    def loop(self):
        self.render()
        while True:
            k = self.win.getkey()
            if k in self.callbacks:
                self.callbacks[k]()
            elif k == 'q':
                self.player.end()
                break
            else:
                pass

PanelState = namedtuple('PanelState', ['top', 'selected_row'])

class MainPanel(object):
    def __init__(self, parent, height, y, plex):
        self.win = curses.newwin(height, curses.COLS, y, 0)
        self.pad = curses.newpad(500, curses.COLS-2)
        self.parent = parent
        self.height = height-1
        self.y = y+1
        self.top = 0
        self.plex = plex
        self.data = []
        self.states = []
        self.register_callbacks()

    @property
    def bottom(self):
        return min(len(self.data), (self.top + self.height)) - 1

    @property
    def lastrow(self):
        return len(self.data)

    def push_state(self):
        self.states.append(PanelState(self.top, self.pad.getyx()[0]))

    def pop_state(self):
        s = self.states.pop()
        self.top = s.top
        self.pad.move(s.selected_row, 0)

    def render(self):
        self.pad.clear()
        self.pad.move(0, 0)
        self.data = self.plex.get()
        y = 0
        for i in range(self.top, self.lastrow):
            y += 1
            try:
                item = self.data[i]
                s = ""
                if item.get('type', None) == 'track':
                    s = "[{:10.3f}s]   {}".format(item['duration'] / 1000., item['title'])
                else:
                    s = "{} >".format(item['title'])
                self.pad.addstr(y, 1, s)
            except Exception as e:
                raise Exception("y is %d, i is %d, self.height is %d" % (y, i, self.height)) from e
        self.refresh(True)

    def refresh(self, all=False):
        if all:
            self.win.border()
            self.win.refresh()
            self.pad.move(0, 0)
        self.pad.refresh(self.top, 0, self.y, 1, self.height, curses.COLS-2)

    def register_callbacks(self):
        self.parent.register_callbacks(('j', curses.KEY_DOWN), self.movehl, 1)
        self.parent.register_callbacks(('k', curses.KEY_UP), self.movehl, -1)
        self.parent.register_callbacks(('l', curses.KEY_RIGHT), self.down)
        self.parent.register_callbacks(('h', curses.KEY_LEFT), self.up)

    def clearhl(self):
        y, x = self.pad.getyx()
        self.nohl(y)

    def down(self):
        y, x = self.pad.getyx()
        item = self.data[y-1]
        if item.get('type', None) == 'track':
            self.parent.play(item)
        else:
            self.clearhl()
            self.plex.down(item['key'])
            self.render()

    def up(self):
        self.plex.up()
        self.render()

    def movehl(self, direction):
        y, x = self.pad.getyx()
        self.selectrow(y, y+direction)

    def scroll(self, new_y):
        if new_y > self.bottom and new_y < self.lastrow:
            self.top += 1
        if new_y < self.top and new_y > 0:
            self.top -= 1

    def selectrow(self, old_y, new_y):
        if new_y < 1 or new_y > self.lastrow:
            return

        self.scroll(new_y)

        if old_y != 0:
            # reset current row
            self.nohl(old_y)
        try:
            self.pad.move(new_y, 0)
        except Exception as e:
            debug("Exception: {!r}".format(e))
        self.hl(new_y)
        self.refresh()

    def nohl(self, row):
        self.hl(row, False)

    def hl(self, row, on=True):
        attr = curses.A_REVERSE if on else curses.A_NORMAL
        self.pad.chgat(row, 1, curses.COLS-2, attr)


class PlayerPanel(object):
    def __init__(self, parent):
        self.win = curses.newwin(3, curses.COLS, curses.LINES-3, 0)
        self.parent = parent
        self.register_callbacks()

    def register_callbacks(self):
        pass

    def render(self):
        self.win.refresh()

    def set_track(self, title, duration):
        self.win.clear()
        self.win.addstr(title + str(duration).rjust(curses.COLS - (len(title) + 4)) + 's')
        self.render()
