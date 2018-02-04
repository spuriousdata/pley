import ctypes
import ctypes.util
from queue import Queue, Empty


libflac = ctypes.cdll.LoadLibrary(ctypes.util.find_library('FLAC'))


# #define's in FLAC/format.h
FLAC__MAX_FIXED_ORDER = 4
FLAC__MAX_LPC_ORDER = 32

# #define's in FLAC/stream_decoder.h
FLAC__MAX_CHANNELS = 8


def c_func(func, restype=None, argtypes=[], errcheck=None):
    f = getattr(libflac, func)
    f.restype = restype
    f.argtypes = argtypes
    if errcheck:
        f.errcheck = errcheck
    return f


def truthcheck(res, func, args):
    if not res:
        raise Exception("%r returned False" % func)
    return res


class StreamDecoder(ctypes.Structure):
    _fields_ = []


class ChannelAssignmentEnum:
    FLAC__CHANNEL_ASSIGNMENT_INDEPENDENT    = 0 #independent channels
    FLAC__CHANNEL_ASSIGNMENT_LEFT_SIDE      = 1 #left+side stereo
    FLAC__CHANNEL_ASSIGNMENT_RIGHT_SIDE     = 2 #right+side stereo
    FLAC__CHANNEL_ASSIGNMENT_MID_SIDE       = 3 #mid+side stereo


class FrameNumberTypeEnum:
    FLAC__FRAME_NUMBER_TYPE_FRAME_NUMBER    = 0 #number contains the frame number
    FLAC__FRAME_NUMBER_TYPE_SAMPLE_NUMBER   = 1 #number contains the sample number of first sample in frame


class Number(ctypes.Union):
    _fields_ = [
        ("frame_number", ctypes.c_uint32),
        ("sample_number", ctypes.c_uint64),
    ]

class FrameHeader(ctypes.Structure):
    _fields_ = [
        ("blocksize", ctypes.c_uint),
        ("sample_rate", ctypes.c_uint),
        ("channels", ctypes.c_uint),
        ("channel_assignment", ctypes.c_int), # ChannelAssignmentEnum
        ("bits_per_sample", ctypes.c_uint),
        ("number_type", ctypes.c_int), # FrameNumberTypeEnum
        ("number", Number),
        ("crc", ctypes.c_uint8),
    ]


class SubframeTypeEnum:
    FLAC__SUBFRAME_TYPE_CONSTANT    = 0 #constant signal
    FLAC__SUBFRAME_TYPE_VERBATIM    = 1 #uncompressed signal
    FLAC__SUBFRAME_TYPE_FIXED       = 2 #fixed polynomial prediction
    FLAC__SUBFRAME_TYPE_LPC         = 3 #linear prediction

class Subframe_Constant(ctypes.Structure):
    _fields_ = [
        ("value", ctypes.c_int32),
    ]


class EntropyCodingMethodTypeEnum:
    FLAC__ENTROPY_CODING_METHOD_PARTITIONED_RICE  = 0 #Residual is coded by partitioning into contexts, each with it's own 4-bit Rice parameter.
    FLAC__ENTROPY_CODING_METHOD_PARTITIONED_RICE2 = 1 #Residual is coded by partitioning into contexts, each with it's own 5-bit Rice parameter.


class EntropyCodingMethod_PartitionedRiceContents(ctypes.Structure):
    _fields_ = [
       ("parameters", ctypes.POINTER(ctypes.c_uint)),
       ("raw_bits", ctypes.POINTER(ctypes.c_uint)),
       ("capacity_by_order", ctypes.c_uint),
    ]


class EntropyCodingMethod_PartitionedRice(ctypes.Structure):
    _fields_ = [
        ("order", ctypes.c_uint),
        ("contents", ctypes.POINTER(EntropyCodingMethod_PartitionedRiceContents)),
    ]


class CodingMethodData(ctypes.Union):
    _fields_ = [
        ("partitioned_rice", EntropyCodingMethod_PartitionedRice),
    ]


class EntropyCodingMethod(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_int), # EntropyCodingMethodTypeEnum
        ("data", CodingMethodData),
    ]


class Subframe_Fixed(ctypes.Structure):
    _fields_ = [
        ("entropy_coding_method", EntropyCodingMethod),
        ("order", ctypes.c_uint),
        ("warmup", ctypes.c_int32 * FLAC__MAX_FIXED_ORDER),
        ("residual", ctypes.POINTER(ctypes.c_int32)),
    ]


class Subframe_LPC(ctypes.Structure):
    _fields_ = [
        ("entropy_coding_method", EntropyCodingMethod),
        ("order", ctypes.c_uint),
        ("qlp_coeff_precision", ctypes.c_uint),
        ("quantization_level", ctypes.c_int),
        ("qlp_coeff", ctypes.c_int32 * FLAC__MAX_LPC_ORDER),
        ("warmup", ctypes.c_int32 * FLAC__MAX_LPC_ORDER),
        ("residual", ctypes.POINTER(ctypes.c_int32)),
    ]


class Subframe_Verbatim(ctypes.Structure):
    _fields_ = [
        ("data", ctypes.POINTER(ctypes.c_int32)),
    ]


class SubframeData(ctypes.Union):
    _fields_ = [
        ("constant", Subframe_Constant),
        ("fixed", Subframe_Fixed),
        ("lpc", Subframe_LPC),
        ("verbatim", Subframe_Verbatim),
    ]


class Subframe(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_int), # SubframeTypeEnum
        ("data", SubframeData),
        ("wasted_bits", ctypes.c_uint),
    ]


class FrameFooter(ctypes.Structure):
    _fields_ = [
        ("crc", ctypes.c_uint16),
    ]


class Frame(ctypes.Structure):
    _fields_ = [
        ("header", FrameHeader),
        #("subframes", Subframe * FLAC__MAX_CHANNELS),
        #("footer", FrameFooter),
    ]


class ReadStatusEnum:
    FLAC__STREAM_DECODER_READ_STATUS_CONTINUE = 0
    FLAC__STREAM_DECODER_READ_STATUS_END_OF_STREAM = 1
    FLAC__STREAM_DECODER_READ_STATUS_ABORT = 2


class WriteStatusEnum:
    FLAC__STREAM_DECODER_WRITE_STATUS_CONTINUE = 0
    FLAC__STREAM_DECODER_WRITE_STATUS_ABORT = 1


class MetadataType:
    FLAC__METADATA_TYPE_STREAMINFO      = 0 # STREAMINFO block
    FLAC__METADATA_TYPE_PADDING         = 1 # PADDING block
    FLAC__METADATA_TYPE_APPLICATION     = 2 # APPLICATION block
    FLAC__METADATA_TYPE_SEEKTABLE       = 3 # SEEKTABLE block
    FLAC__METADATA_TYPE_VORBIS_COMMENT  = 4 # VORBISCOMMENT block (a.k.a. FLAC tags)
    FLAC__METADATA_TYPE_CUESHEET        = 5 # CUESHEET block
    FLAC__METADATA_TYPE_PICTURE         = 6 # PICTURE block
    FLAC__METADATA_TYPE_UNDEFINED       = 7 # marker to denote beginning of undefined type range; this number will increase as new metadata types are added
    FLAC__MAX_METADATA_TYPE             = 8 # No type will ever be greater than this. There is not enough room in the protocol block.


class StreamMetadata_StreamInfo(ctypes.Structure):
    _fields_ = [
        ("min_blocksize", ctypes.c_uint),
        ("max_blocksize", ctypes.c_uint),
        ("min_framesize", ctypes.c_uint),
        ("max_framesize", ctypes.c_uint),
        ("sample_rate", ctypes.c_uint),
        ("channels", ctypes.c_uint),
        ("bits_per_sample", ctypes.c_uint),
        ("total_samples", ctypes.c_uint64),
        ("md5sum", ctypes.c_byte * 16),
    ]


class MetadataData(ctypes.Union):
    _fields_ = [
        ("stream_info", StreamMetadata_StreamInfo),
#        ("padding", StreamMetadata_Padding),
#        ("application", StreamMetadata_Application),
#        ("seek_table", StreamMetadata_SeekTable),
#        ("vorbis_comment", StreamMetadata_VorbisComment),
#        ("cue_sheet", StreamMetadata_CueSheet),
#        ("picture", StreamMetadata_Picture),
#        ("unknown", StreamMetadata_Unknown),
    ]

class StreamMetadata(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_int), # MetadataType
        ("is_last", ctypes.c_int),
        ("length", ctypes.c_uint),
        ("data", MetadataData),
    ]


read_callback_type = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.POINTER(StreamDecoder),
                                      ctypes.POINTER(ctypes.c_byte),
                                      ctypes.POINTER(ctypes.c_size_t),
                                      ctypes.py_object)

write_callback_type = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.POINTER(StreamDecoder),
                                       ctypes.POINTER(Frame),
                                       ctypes.POINTER(ctypes.POINTER(ctypes.c_int)),
                                       ctypes.py_object)

metadata_callback_type = ctypes.CFUNCTYPE(None, ctypes.POINTER(StreamDecoder),
                                       ctypes.POINTER(StreamMetadata),
                                       ctypes.py_object)

error_callback_type = ctypes.CFUNCTYPE(None, ctypes.POINTER(StreamDecoder),
                                     ctypes.c_int, ctypes.py_object)


class FlacDecoder(object):
    def __init__(self):
        self.__queue = Queue()
        self.__streaminfo = None
        self.__decoder = c_func('FLAC__stream_decoder_new', ctypes.POINTER(StreamDecoder))()
        _init = c_func('FLAC__stream_decoder_init_stream',
                       None,
                       [ctypes.POINTER(StreamDecoder),
                        read_callback_type,
                        ctypes.POINTER(None),
                        ctypes.POINTER(None),
                        ctypes.POINTER(None),
                        ctypes.POINTER(None),
                        write_callback_type,
                        ctypes.POINTER(None),
                        error_callback_type,
                        ctypes.py_object])

        self.process_func = c_func('FLAC__stream_decoder_process_until_end_of_stream',
                                   ctypes.c_int, [ctypes.POINTER(StreamDecoder)])
        self.process_metadata_func = c_func('FLAC__stream_decoder_process_until_end_of_metadata',
                                            ctypes.c_int, [ctypes.POINTER(StreamDecoder)],
                                            truthcheck)
        self.reset_func = c_func('FLAC__stream_decoder_reset',
                                 None, [ctypes.POINTER(StreamDecoder)])
        self.finish_func = c_func('FLAC__stream_decoder_finish', ctypes.c_int,
                                  [ctypes.POINTER(StreamDecoder)])
        self.delete_func = c_func('FLAC__stream_decoder_delete', None,
                                  [ctypes.POINTER(StreamDecoder)])

        self.__continue = True
        self.__buffer = bytearray()
        _init(self.__decoder,
              read_callback_type(FlacDecoder.read_callback),
              None, # FlacDecoder.seek_callback,
              None, # FlacDecoder.tell_callback,
              None, # FlacDecoder.length_callback,
              None, # FlacDecoder.eof_callback,
              write_callback_type(FlacDecoder.write_callback),
              None, # metadata_callback_type(FlacDecoder.metadata_callback),
              error_callback_type(FlacDecoder.error_callback),
              ctypes.py_object(self))

    def get_metadata(self):
        return None
        """ This doesn't work """
        self.__fill_buffer()
        if not self.process_metadata_func(self.__decoder):
            raise Exception("process_metadata_func returned False, len(buf) is %d" % len(self.__buffer))
        return self.__streaminfo

    def play(self, callback):
        self.__continue = True
        self.play_callback = callback
        self.__fill_buffer()
        if not self.process_func(self.__decoder):
            raise Exception("StreamDecoder process returned False, len(buf) is %d" % len(self.__buffer))

    def __fill_buffer(self):
        block = False
        if len(self.__buffer) == 0:
            block = True
        try:
            data = self.__queue.get(block)
        except Empty:
            return
        if data is None:
            return
        self.__buffer.extend(data)

    def stop(self):
        self.__continue = False

    def reset(self):
        self.__buffer.clear()
        self.__streaminfo = None
        self.reset_func(self.__decoder)

    @property
    def keep_playing(self):
        return self.__continue

    @property
    def queue(self):
        return self.__queue

    def read(self, length):
        data = memoryview(self.__buffer)[:length]
        self.__buffer = self.__buffer[length:]
        return data

    def finish(self):
        self.finish_func(self.__decoder)

    def __del__(self):
        self.finish()
        self.delete_func(self.__decoder)

    @staticmethod
    def read_callback(decoder, _buf, length, self):
        ret = ReadStatusEnum.FLAC__STREAM_DECODER_READ_STATUS_CONTINUE
        l = length[0]
        tmp = self.read(l)
        if len(tmp) != l:
            length[0] = len(tmp)
            ret = ReadStatusEnum.FLAC__STREAM_DECODER_READ_STATUS_END_OF_STREAM
        ctypes.memmove(_buf, tmp.tobytes(), length[0])
        tmp.release()
        self.__fill_buffer()
        return ret

    @staticmethod
    def write_callback(decoder, _frame, _buf, self):
        if self.keep_playing:
            d = bytearray()
            for b in range(0, _frame[0].header.blocksize):
                for c in range(0, _frame[0].header.channels):
                    d.extend(_buf[c][b].to_bytes(2, byteorder='little', signed=True))
            self.play_callback(bytes(d))
            return WriteStatusEnum.FLAC__STREAM_DECODER_WRITE_STATUS_CONTINUE
        else:
            return WriteStatusEnum.FLAC__STREAM_DECODER_WRITE_STATUS_ABORT

    @staticmethod
    def metadata_callback(decoder, metadata, self):
        if metadata[0].type == MetadataType.FLAC__METADATA_TYPE_STREAMINFO:
            self.__streaminfo = {
                'channels': metadata[0].data.stream_info.channels,
                'sample_rate': metadata[0].data.stream_info.sample_rate,
                'bits': metadata[0].data.stream_info.bits_per_sample,
            }

    @staticmethod
    def error_callback(decoder, status, self):
        pass


if __name__ == '__main__':
    f = FlacDecoder()
    with open("/mnt/media/Audio/owned/16_48/The Who/Who's Next (Deluxe Edition)/01-Baba O'Riley.flac", "rb") as fp:
        f.queue.put(fp.read())
    from pley.output.oss import Device
    import pudb; pu.db
    d = Device()
    #print("Metadata: %r" % f.get_metadata())
    f.play(d.write)
