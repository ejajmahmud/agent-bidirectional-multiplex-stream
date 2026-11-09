"""Unit tests for agent-bidirectional-multiplex-stream."""
import unittest
from agent_bidirectional_multiplex_stream.multiplex import StreamMultiplexer, FrameType


class TestStreamMultiplexer(unittest.TestCase):
    def setUp(self):
        self.mux = StreamMultiplexer(max_chunk_size=10)

    def test_encode_and_decode(self):
        frames = self.mux.send_chunk(42, b"1234567890abcdef", FrameType.DATA)
        self.assertEqual(len(frames), 2)  # 16 bytes split into 10 + 6

        wire = b"".join(frames)
        demux = StreamMultiplexer()
        results = demux.receive_wire_data(wire)
        self.assertEqual(len(results), 2)
        self.assertEqual(demux.get_channel_data(42), b"1234567890abcdef")

    def test_multiple_channels_interleaved(self):
        f1 = self.mux.send_chunk(1, b"AGENT_ONE")
        f2 = self.mux.send_chunk(2, b"AGENT_TWO")
        wire = f1[0] + f2[0]

        demux = StreamMultiplexer()
        demux.receive_wire_data(wire)
        self.assertEqual(demux.get_channel_data(1), b"AGENT_ONE")
        self.assertEqual(demux.get_channel_data(2), b"AGENT_TWO")
