import importlib
from threading import Thread, Event
from pley.formats.flac import FlacDecoder
from pley import config


class Player(object):
    def __init__(self, panel, plex):
        self.panel = panel
        self.plex = plex
        self.stopevent = Event()
        self.thread = None

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

    def callback(self, data):
        self.soundcard.write(data)

    def run(self, response, decoder):
        for data in response.iter_content(8192):
            if self.stopevent.is_set():
                return
            decoder.add_data(data)

        meta = decoder.get_metadata()
        if meta:
            self.soundcard.samplerate(meta['sample_rate'])
            self.soundcard.channels(meta['channels'])

        decoder.play(self.callback)


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
