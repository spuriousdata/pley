import ossaudiodev


class Device(object):
    def __init__(self, device='/dev/dsp1', samplerate=48000, channels=2, fmt=ossaudiodev.AFMT_S16_LE):
        self.adev = ossaudiodev.open(device, 'w')
        self.adev.setfmt(fmt)
        self.adev.speed(samplerate)
        self.adev.channels(channels)

    def write(self, data):
        self.adev.write(data)

    def channels(self, c):
        self.adev.channels(c)

    def samplerate(self, rate):
        self.adev.speed(rate)

    def __del__(self):
        self.adev.close()
