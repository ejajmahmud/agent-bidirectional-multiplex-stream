"""Core Bidirectional Multiplex Stream implementation."""
import struct
import io
from enum import IntEnum
from typing import Dict, List, Tuple, Optional, Any


class FrameType(IntEnum):
    DATA = 1
    CONTROL = 2
    HEARTBEAT = 3
    CLOSE = 4


class Frame:
    # Header format: ChannelID (uint16), FrameType (uint8), PayloadLength (uint32) = 7 bytes
    HEADER_FORMAT = "!HBI"
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

    def __init__(self, channel_id: int, frame_type: FrameType, payload: bytes):
        self.channel_id = channel_id
        self.frame_type = frame_type
        self.payload = payload

    def encode(self) -> bytes:
        header = struct.pack(self.HEADER_FORMAT, self.channel_id, int(self.frame_type), len(self.payload))
        return header + self.payload

    @classmethod
    def decode_from(cls, stream: io.BytesIO) -> Optional['Frame']:
        header_bytes = stream.read(cls.HEADER_SIZE)
        if len(header_bytes) < cls.HEADER_SIZE:
            return None
        channel_id, frame_type_int, payload_len = struct.unpack(cls.HEADER_FORMAT, header_bytes)
        payload = stream.read(payload_len)
        return cls(channel_id, FrameType(frame_type_int), payload)


class StreamMultiplexer:
    def __init__(self, max_chunk_size: int = 1024):
        self.max_chunk_size = max_chunk_size
        self.channel_buffers: Dict[int, bytearray] = {}

    def send_chunk(self, channel_id: int, data: bytes, frame_type: FrameType = FrameType.DATA) -> List[bytes]:
        frames = []
        offset = 0
        if len(data) == 0:
            f = Frame(channel_id, frame_type, b"")
            frames.append(f.encode())
            return frames

        while offset < len(data):
            chunk = data[offset : offset + self.max_chunk_size]
            f = Frame(channel_id, frame_type, chunk)
            frames.append(f.encode())
            offset += len(chunk)
        return frames

    def receive_wire_data(self, wire_bytes: bytes) -> List[Tuple[int, FrameType, bytes]]:
        stream = io.BytesIO(wire_bytes)
        received_frames = []
        while True:
            frame = Frame.decode_from(stream)
            if not frame:
                break
            received_frames.append((frame.channel_id, frame.frame_type, frame.payload))
            if frame.channel_id not in self.channel_buffers:
                self.channel_buffers[frame.channel_id] = bytearray()
            self.channel_buffers[frame.channel_id].extend(frame.payload)
        return received_frames

    def get_channel_data(self, channel_id: int) -> bytes:
        return bytes(self.channel_buffers.get(channel_id, b""))

    def clear_channel(self, channel_id: int):
        if channel_id in self.channel_buffers:
            del self.channel_buffers[channel_id]
