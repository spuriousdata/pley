import ossaudiodev


class Device(object):
    def __init__(self, device='/dev/dsp1', samplerate=48000, channels=2, bits=16):
        self.adev = ossaudiodev.open(device, 'w')
        self.bits(bits)
        self.samplerate(samplerate)
        self.channels(channels)

    def write(self, data):
        return self.adev.write(data)

    def bits(self, bits, signed=True):
        s = "S" if signed else "U"
        fmt = "AFMT_%s%d_LE" % (s, bits)
        try:
            ret = bits
            self.adev.setfmt(getattr(ossaudiodev, fmt))
        except:
            return self.bits(bits-8, signed)
        return ret

    def channels(self, c):
        return self.adev.channels(c)

    def samplerate(self, rate):
        return self.adev.speed(rate)

    def __del__(self):
        self.adev.close()
