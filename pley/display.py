import curses
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


class MainPanel(object):
    def __init__(self, parent, height, y, plex):
        self.outerwin = curses.newwin(height, curses.COLS, y, 0)
        self.outerwin.border()
        self.outerwin.refresh()
        self.win = curses.newpad(500, curses.COLS-2)
        self.lines = 0
        self.y = y+1
        self.height = height - 1
        self.plex = plex
        self.data = None
        self.bottom = -1
        self.parent = parent
        self.register_callbacks()

    def render(self):
        self.win.clear()
        # reset the cursor
        self.win.move(0, 0)
        y = 0
        self.data = self.plex.get()
        self.bottom = len(self.data)
        for item in [x['title'] for x in self.data]:
            y += 1
            try:
                self.win.addstr(y, 1, "{} >".format(item))
            except Exception as e:
                raise Exception("y is %d, self.height is %d" % (y, self.height)) from e
        self.win.move(0, 0)
        self.win.refresh(0, 0, self.y, 1, self.height, curses.COLS-2)

    def register_callbacks(self):
        self.parent.register_callbacks(('j', curses.KEY_DOWN), self.movehl, 1)
        self.parent.register_callbacks(('k', curses.KEY_UP), self.movehl, -1)
        self.parent.register_callbacks(('l', curses.KEY_RIGHT), self.down)
        self.parent.register_callbacks(('h', curses.KEY_LEFT), self.up)

    def clearhl(self):
        y, x = self.win.getyx()
        self.nohl(y)

    def down(self):
        y, x = self.win.getyx()
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
        y, x = self.win.getyx()
        self.selectrow(y, y+direction)

    def selectrow(self, old_y, new_y):
        if new_y < 1 or new_y > self.bottom:
            return

        if old_y != 0:
            # reset current row
            self.nohl(old_y)
        try:
            self.win.move(new_y, 0)
        except Exception as e:
            debug("Exception: {!r}".format(e))
        self.hl(new_y)
        self.win.refresh(0, 0, self.y, 1, self.height, curses.COLS-2)

    def nohl(self, row):
        self.hl(row, False)

    def hl(self, row, on=True):
        attr = curses.A_REVERSE if on else curses.A_NORMAL
        self.win.chgat(row, 1, curses.COLS-2, attr)


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
