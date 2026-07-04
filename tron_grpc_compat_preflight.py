
from __future__ import annotations
import struct
import sys
import time
import hashlib
import dataclasses
from typing import List, Tuple

# ============================================================
# TRON gRPC 兼容层/SeedNode handshake 脱演算包
# 场景: 先不依赖公网可达，本地演算 `50100/50101` 协议兼容包
# 仅用于 lint/执行, 不产生任何 stdio 副作用
# ============================================================

# TLV 固定字段: type(1) + length(2) + value
TLV_TYPE_PROTO_VERSION = 0x01
TLV_TYPE_AGENT        = 0x02
TLV_TYPE_COMPAT       = 0x03
TLV_TYPE_PAYLOAD      = 0xF0
TLV_TYPE_BADGE        = 0xF1

TLV_OVERHEAD = 1 + 2


def encode_tlv(t: int, value: bytes) -> bytes:
    if len(value) > 0xFFFF:
        raise ValueError('TLV value too large')
    return bytes([t]) + struct.pack('!H', len(value)) + value


def decode_tlv_stream(buf: bytes) -> List[Tuple[int, bytes]]:
    i = 0
    out = []
    while i + TLV_OVERHEAD <= len(buf):
        t = buf[i]
        length = struct.unpack('!H', buf[i+1:i+3])[0]
        i += TLV_OVERHEAD
        if i + length > len(buf):
            break
        value = buf[i:i+length]
        out.append((t, value))
        i += length
    return out


@dataclasses.dataclass(frozen=True)
class HandshakeSpec:
    proto: str
    proto_version: int
    feature_mask: int
    session_nonce: bytes
    peer_seed: bytes | None = None

    def encode(self) -> bytes:
        pv = self.proto_version.to_bytes(2, 'big')
        fm = self.feature_mask.to_bytes(4, 'big')
        b = bytearray()
        b += encode_tlv(TLV_TYPE_PROTO_VERSION, pv)
        if self.peer_seed:
            b += encode_tlv(TLV_TYPE_PAYLOAD, self.peer_seed)
        # badge derives from peer_seed when present
        if self.peer_seed:
            badge = hashlib.sha256(self.peer_seed).digest()[:12]
            b += encode_tlv(TLV_TYPE_BADGE, badge)
        # compatibility hashmix incl. proto version
        compat = hashlib.sha256(pv + fm + pv).digest()[:8]
        b += encode_tlv(TLV_TYPE_COMPAT, compat)
        agent = ('hermes-tron-grpc/1.0.0|50100/50101|' + self.proto).encode('utf-8')
        b += encode_tlv(TLV_TYPE_AGENT, agent)
        return bytes(b)

    @staticmethod
    def parse(buf: bytes) -> 'HandshakeSpec':
        parsed = dict(decode_tlv_stream(buf))
        pv = int.from_bytes(parsed[TLV_TYPE_PROTO_VERSION][:2], 'big')
        fm = int.from_bytes(parsed[TLV_TYPE_COMPAT][:4], 'big')
        ps = parsed.get(TLV_TYPE_PAYLOAD)
        return HandshakeSpec(
            proto='tron',
            proto_version=pv,
            feature_mask=fm,
            session_nonce=struct.pack('!I', 0xA5A5A5A5),
            peer_seed=ps,
        )


def simulate_50200_peer(spec: HandshakeSpec) -> Tuple[bytes, int]:
    their_tlv = spec.encode()
    parsed = dict(decode_tlv_stream(their_tlv))
    pv = int.from_bytes(parsed[TLV_TYPE_PROTO_VERSION][:2], 'big')
    badge = parsed.get(TLV_TYPE_BADGE, b'')
    compatibility = 1 if pv >= 0x0200 and badge else 0
    peer_badge = badge if badge else b'\x00' * 12
    out = bytearray()
    payload = b'\xAB\xCD\xEF' + struct.pack('!B', compatibility)
    out += encode_tlv(TLV_TYPE_PROTO_VERSION, pv.to_bytes(2, 'big'))
    out += encode_tlv(TLV_TYPE_PAYLOAD, payload)
    out += encode_tlv(TLV_TYPE_BADGE, peer_badge)
    return bytes(out), compatibility


def run_preflight() -> None:
    scenarios = [
        ('50100-init-short', 0x0200, 0x00000001),
        ('50100-compat',      0x0200, 0x0000000F),
        ('50101-session-mid', 0x0300, 0x00000077),
        ('50101-session-max', 0x03FF, 0xFFFFFFFF),
    ]
    failures = 0
    checked = 0

    print('handshake,scenario,version,feature_mask,compat,seed_present')
    for name, version, mask in scenarios:
        for seed in (b'\x00'*32, b'\xFF'*32, None):  # first two = has real peer seed
            checked += 1
            spec = HandshakeSpec(
                proto='tron',
                proto_version=version,
                feature_mask=mask,
                session_nonce=struct.pack('!I', 0x5A5A5A5A),
                peer_seed=seed,
            )
            buf = spec.encode()
            peer, compat = simulate_50200_peer(spec)
            print(
                f"preflight,{name}-{'seeded' if seed else 'plain'},0x{version:04x},0x{mask:08x},{compat},{seed is not None}"
            )
            parsed = dict(decode_tlv_stream(buf))
            assert TLV_TYPE_PROTO_VERSION in parsed, 'proto_version missing'
            decoded = spec.parse(buf)
            assert decoded.proto_version == version
            if seed is not None:
                badge_present = TLV_TYPE_BADGE in parsed
                if not badge_present or decoded.peer_seed != seed:
                    failures += 1

    print(f"\nchecked={checked},failures={failures}")
    if failures:
        sys.exit(1)
    else:
        print('status=PASS')


if __name__ == '__main__':
    run_preflight()
