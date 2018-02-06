from cflac cimport *
from libc.string cimport memmove
from threading import Lock


cdef FLAC__StreamDecoderReadStatus read_cb(const FLAC__StreamDecoder *decoder, uint8_t buffer[], size_t *bytes, void *client_data) except -1:
    cdef FLAC__StreamDecoderReadStatus ret = FLAC__StreamDecoderReadStatus.FLAC__STREAM_DECODER_READ_STATUS_CONTINUE
    py_decoder = <FlacDecoder>client_data
    mv = py_decoder.read(bytes[0])
    cdef uint8_t[:] tmp = mv
    if len(tmp) != bytes[0]:
        bytes[0] = len(tmp)
        ret = FLAC__StreamDecoderReadStatus.FLAC__STREAM_DECODER_READ_STATUS_END_OF_STREAM
    memmove(buffer, &tmp[0], bytes[0])
    mv.release()
    return ret


cdef FLAC__StreamDecoderWriteStatus write_cb(const FLAC__StreamDecoder *decoder, const FLAC__Frame *frame, const int32_t *const buffer[], void *client_data):
    py_decoder = <FlacDecoder>client_data
    if py_decoder.keep_playing:
        d = bytearray()
        for b in range(0, frame[0].header.blocksize):
            for c in range(0, frame[0].header.channels):
                d.extend(buffer[c][b].to_bytes(2, byteorder='little', signed=True))
        py_decoder.play_callback(bytes(d))
        return FLAC__StreamDecoderWriteStatus.FLAC__STREAM_DECODER_WRITE_STATUS_CONTINUE
    else:
        return FLAC__StreamDecoderWriteStatus.FLAC__STREAM_DECODER_WRITE_STATUS_ABORT


cdef void metadata_cb(const FLAC__StreamDecoder *decoder, const FLAC__StreamMetadata *metadata, void *client_data):
    py_decoder = <FlacDecoder>client_data
    if metadata[0].type == FLAC__MetadataType.FLAC__METADATA_TYPE_STREAMINFO:
        py_decoder.set_streaminfo({
            'channels': metadata[0].data.stream_info.channels,
            'sample_rate': metadata[0].data.stream_info.sample_rate,
            'bits': metadata[0].data.stream_info.bits_per_sample,
        })


cdef void error_cb(const FLAC__StreamDecoder *decoder, FLAC__StreamDecoderErrorStatus status, void *client_data):
    pass


cdef class FlacDecoder(object):
    cdef FLAC__StreamDecoder *__decoder
    cdef bytearray __buffer
    cdef object __lock
    cdef object __continue
    cdef object __streaminfo
    cdef object play_callback

    def __cinit__(self):
        self.__decoder = FLAC__stream_decoder_new()

    def __init__(self):
        self.__buffer = bytearray()
        self.__lock = Lock()
        self.__continue = True

        FLAC__stream_decoder_init_stream(self.__decoder, read_cb, NULL, NULL,
            NULL, NULL, write_cb, metadata_cb, error_cb, <void*>self)

    def add_data(self, data):
        with self.__lock:
            self.__buffer.extend(data)

    def read(self, size_t length):
        with self.__lock:
            data = memoryview(self.__buffer)[:length]
            self.__buffer = self.__buffer[length:]
            return data

    def finish(self):
        FLAC__stream_decoder_finish(self.__decoder)

    @property
    def keep_playing(self):
        return self.__continue

    def stop(self):
        self.__continue = False

    def play(self, callback):
        self.__continue = True
        self.play_callback = callback
        if not FLAC__stream_decoder_process_until_end_of_stream(self.__decoder):
            raise Exception("StreamDecoder process returned False, len(buf) is %d" % len(self.__buffer))

    def reset(self):
        FLAC__stream_decoder_reset(self.__decoder)

    cdef set_streaminfo(self, si):
        self.__streaminfo = si

    def get_metadata(self):
        if not FLAC__stream_decoder_process_until_end_of_metadata(self.__decoder):
            raise Exception("process_metadata_func returned False, len(buf) is %d" % len(self.__buffer))
        return self.__streaminfo

    def __dealloc__(self):
        FLAC__stream_decoder_finish(self.__decoder)
        FLAC__stream_decoder_delete(self.__decoder)
