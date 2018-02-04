import importlib
from threading import Thread, Event
from pley.formats.flac import FlacDecoder
from pley import config


class Player(object):
    def __init__(self, panel, plex):
        self.panel = panel
        self.plex = plex
        self.stopevent = Event()
        self.decoders = {
            'flac': FlacDecoder(),
        }
        amod = importlib.import_module('pley.output.' + config.get('sound.module'))
        Device = getattr(amod, 'Device')
        self.soundcard = Device(config.get('sound.device'))

    def render(self):
        self.panel.render()

    def stop(self):
        self.stopevent.set()
        for d in self.decoders:
            del d

    def play(self, item):
        t = "%(grandparentTitle)s - %(parentTitle)s - %(title)s" % item
        self.panel.set_track(t, item['duration'] / 1000)
        for part in item['Media']:
            for stream in part['Part']:
                decoder = self.decoders[stream['container']]
                self.stopevent.set()
                decoder.reset()
                fetcher = Thread(target=self.download,
                                 args=(self.plex.stream(stream['key']), decoder))
                self.stopevent.clear()
                fetcher.start()
                meta = [x for x in stream['Stream'] if x.get('streamType', 0) == 2]
                if meta:
                    meta = meta[0]
                    self.soundcard.samplerate(meta['samplingRate'])
                    self.soundcard.channels(meta['channels'])
                decoder.play(self.soundcard.write)

    def download(self, response, decoder):
        q = decoder.queue
        for data in response.iter_content(8192):
            if self.stopevent.is_set():
                return
            q.put(data)
        q.put(None)
