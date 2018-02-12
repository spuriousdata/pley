import importlib
import audioop
from threading import Thread, Event
from functools import partial
from pley.formats.flac import FlacDecoder
from pley import config


class Player(object):
    def __init__(self, panel, plex):
        self.panel = panel
        self.plex = plex
        self.stopevent = Event()
        self.thread = None
        self.meta = None

        amod = importlib.import_module('pley.output.' + config.get('sound.module'))
        Device = getattr(amod, 'Device')
        self.soundcard = Device(config.get('sound.device'))

        self.active_decoder = None
        self.decoders = {
            'flac': FlacDecoder(),
        }

    def render(self):
        self.panel.render()

    def stop(self):
        self.stopevent.set()
        if self.active_decoder:
            self.active_decoder.stop()

    def end(self):
        self.stopevent.set()
        for d in self.decoders:
            del d

    def play(self, item):
        t = "%(grandparentTitle)s - %(parentTitle)s - %(title)s" % item
        self.panel.set_track(t, item['duration'] / 1000)
        for part in item['Media']:
            for stream in part['Part']:
                self.stopevent.set()
                self.active_decoder = self.decoders[stream['container']]
                self.active_decoder.reset()
                self.thread = Thread(target=self.run,
                                 args=(
                                     self.plex.stream(stream['key']),
                                     self.active_decoder))
                self.stopevent.clear()
                self.thread.start()

    def callback(self, data, bits=0, samplerate=0, channels=0, newrate=0, newwidth=0):
        newdata = data[:]
        if samplerate != newrate:
            (newdata, s) = audioop.ratecv(newdata, int(bits / 8), channels, samplerate, newrate, None)
        if bits != newwidth:
            newdata = audioop.lin2lin(newdata, int(bits / 8), int(newwidth / 8))
        self.soundcard.write(newdata)

    def run(self, response, decoder):
        for data in response.iter_content(8192):
            if self.stopevent.is_set():
                return
            decoder.add_data(data)

        self.meta = decoder.get_metadata()

        self.soundcard.channels(self.meta.channels)
        rate = self.soundcard.samplerate(self.meta.samplerate)
        bits = self.soundcard.bits(self.meta.bits)

        cb = partial(self.callback, bits=self.meta.bits,
                samplerate=self.meta.samplerate, channels=self.meta.channels,
                newrate=rate, newwidth=bits)

        decoder.play(cb)


if __name__ == '__main__':
    from pley.api import Plex
    config.init()
    class MockPanel(object):
        def render(self):
            pass
        def set_track(self, *args, **kwargs):
            pass
    plex = Plex(config.get('host'), config.get('token'))
    plex.down('17')
    plex.down('all')
    plex.down('/library/metadata/81327/children')
    plex.down('/library/metadata/81341/children')
    plex.down('/library/metadata/81342')
    player = Player(MockPanel(), plex)
    player.play(plex.get()[0])
