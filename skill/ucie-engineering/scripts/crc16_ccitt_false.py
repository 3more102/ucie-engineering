#!/usr/bin/env python3
"""Generic CRC-16/CCITT-FALSE reference calculator; not a UCIe CRC model."""
import argparse


def crc16_ccitt_false(data: bytes) -> int:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("hex_bytes", help="Hex bytes, e.g. 313233343536373839")
    args = parser.parse_args()
    data = bytes.fromhex(args.hex_bytes)
    print(f"CRC-16/CCITT-FALSE: 0x{crc16_ccitt_false(data):04X}")
    print("Reminder: this generic model is not UCIe-specific.")


if __name__ == "__main__":
    main()
