"""CLI for agent-bidirectional-multiplex-stream."""
import sys
import argparse
from .multiplex import StreamMultiplexer, FrameType


def main():
    parser = argparse.ArgumentParser(description="Agent Bidirectional Multiplex Stream CLI")
    parser.add_argument("--demo", action="store_true", help="Run multiplex streaming demonstration")
    args = parser.parse_args()

    if args.demo:
        mux = StreamMultiplexer(max_chunk_size=16)
        wire = bytearray()

        # Send interleaved data on 2 channels
        frames1 = mux.send_chunk(1, b"Hello from Agent 1 (Token Stream)")
        frames2 = mux.send_chunk(2, b"Executing tool: run_code")

        # Interleave on the wire
        for f1, f2 in zip(frames1, frames2):
            wire.extend(f1)
            wire.extend(f2)
        # Any remaining
        for f in frames1[len(frames2):] + frames2[len(frames1):]:
            wire.extend(f)

        print(f"Multiplexed {len(wire)} bytes across 2 channels.")
        demux = StreamMultiplexer()
        demux.receive_wire_data(bytes(wire))
        print("Demultiplexed Channel 1:", demux.get_channel_data(1).decode())
        print("Demultiplexed Channel 2:", demux.get_channel_data(2).decode())
    else:
        parser.print_help()
    sys.exit(0)


if __name__ == "__main__":
    main()
