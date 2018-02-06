from libc.stdint cimport *


cdef extern from "FLAC/format.h":
    ctypedef struct FLAC__METADATA_TYPE_STREAMINFO:
        unsigned min_blocksize
        unsigned max_blocksize
        unsigned min_framesize
        unsigned max_framesize
        unsigned sample_rate
        unsigned channels
        unsigned bits_per_sample
        uint64_t total_samples
        uint8_t  md5sum[16]

    ctypedef union FLAC__StreamMetadataData:
        FLAC__METADATA_TYPE_STREAMINFO stream_info

    ctypedef struct FLAC__StreamMetadata:
        FLAC__MetadataType type
        bint is_last
        unsigned length
        FLAC__StreamMetadataData data


cdef extern from "FLAC/stream_decoder.h":
    ctypedef struct FLAC__StreamDecoder:
        pass

    ctypedef enum FLAC__ChannelAssignment:
        FLAC__CHANNEL_ASSIGNMENT_INDEPENDENT    #independent channels
        FLAC__CHANNEL_ASSIGNMENT_LEFT_SIDE      #left+side stereo
        FLAC__CHANNEL_ASSIGNMENT_RIGHT_SIDE     #right+side stereo
        FLAC__CHANNEL_ASSIGNMENT_MID_SIDE       #mid+side stereo

    ctypedef enum FLAC__StreamDecoderReadStatus:
        FLAC__STREAM_DECODER_READ_STATUS_CONTINUE
        FLAC__STREAM_DECODER_READ_STATUS_END_OF_STREAM
        FLAC__STREAM_DECODER_READ_STATUS_ABORT

    ctypedef enum FLAC__StreamDecoderWriteStatus:
        FLAC__STREAM_DECODER_WRITE_STATUS_CONTINUE
        FLAC__STREAM_DECODER_WRITE_STATUS_ABORT

    ctypedef enum FLAC__StreamDecoderErrorStatus:
        FLAC__STREAM_DECODER_ERROR_STATUS_LOST_SYNC
        FLAC__STREAM_DECODER_ERROR_STATUS_BAD_HEADER
        FLAC__STREAM_DECODER_ERROR_STATUS_FRAME_CRC_MISMATCH
        FLAC__STREAM_DECODER_ERROR_STATUS_UNPARSEABLE_STREAM

    ctypedef enum FLAC__StreamDecoderInitStatus:
        FLAC__STREAM_DECODER_INIT_STATUS_OK
        FLAC__STREAM_DECODER_INIT_STATUS_UNSUPPORTED_CONTAINER
        FLAC__STREAM_DECODER_INIT_STATUS_INVALID_CALLBACKS
        FLAC__STREAM_DECODER_INIT_STATUS_MEMORY_ALLOCATION_ERROR
        FLAC__STREAM_DECODER_INIT_STATUS_ERROR_OPENING_FILE
        FLAC__STREAM_DECODER_INIT_STATUS_ALREADY_INITIALIZED

    ctypedef enum FLAC__MetadataType:
        FLAC__METADATA_TYPE_STREAMINFO
        FLAC__METADATA_TYPE_PADDING
        FLAC__METADATA_TYPE_APPLICATION
        FLAC__METADATA_TYPE_SEEKTABLE
        FLAC__METADATA_TYPE_VORBIS_COMMENT
        FLAC__METADATA_TYPE_CUESHEET
        FLAC__METADATA_TYPE_PICTURE
        FLAC__METADATA_TYPE_UNDEFINED
        FLAC__MAX_METADATA_TYPE

    ctypedef struct FLAC__FrameHeader:
        unsigned blocksize
        unsigned sample_rate
        unsigned channels

    ctypedef struct FLAC__Frame:
        FLAC__FrameHeader header

    ctypedef FLAC__StreamDecoderReadStatus(* FLAC__StreamDecoderReadCallback)(const FLAC__StreamDecoder *decoder, uint8_t buffer[], size_t *bytes, void *client_data)
    ctypedef FLAC__StreamDecoderWriteStatus(* FLAC__StreamDecoderWriteCallback)(const FLAC__StreamDecoder *decoder, const FLAC__Frame *frame, const int32_t *const buffer[], void *client_data)
    ctypedef void(* FLAC__StreamDecoderMetadataCallback)(const FLAC__StreamDecoder *decoder, const FLAC__StreamMetadata *metadata, void *client_data)
    ctypedef void(* FLAC__StreamDecoderErrorCallback)(const FLAC__StreamDecoder *decoder, FLAC__StreamDecoderErrorStatus status, void *client_data)


    bint FLAC__stream_decoder_process_until_end_of_stream(FLAC__StreamDecoder *decoder)
    bint FLAC__stream_decoder_process_until_end_of_metadata(FLAC__StreamDecoder *decoder)
    bint FLAC__stream_decoder_reset(FLAC__StreamDecoder *decoder)
    bint FLAC__stream_decoder_finish(FLAC__StreamDecoder *decoder)
    void FLAC__stream_decoder_delete(FLAC__StreamDecoder *decoder)
    FLAC__StreamDecoder *FLAC__stream_decoder_new()
    FLAC__StreamDecoderInitStatus FLAC__stream_decoder_init_stream(
            FLAC__StreamDecoder                *decoder,
            FLAC__StreamDecoderReadCallback     read_callback,
            void *,
            void *,
            void *,
            void *,
            FLAC__StreamDecoderWriteCallback    write_callback,
            FLAC__StreamDecoderMetadataCallback metadata_callback,
            FLAC__StreamDecoderErrorCallback    error_callback,
            void                               *client_data
        )
