#!/usr/bin/env python3
"""tron_seednode_handshake.py
简化版 SeedNode 握手器 (50100/50101)
1) 向本机 50100/50101 发送 TLV 握手包
2) 等待对方回包
3) 输出窗口级状态，不依赖公网
"""
from __future__ import annotations
import socket
import struct
import sys
import os
import time
import hashlib

HOST = '127.0.0.1'
TIMEOUT = float(os.environ.get('SEEDHANDSHAKE_TIMEOUT', '2.0'))
PORT = int(os.environ.get('SEEDHANDSHAKE_PORT', '50100'))

import tron_grpc_compat_preflight as pp


def build_handshake(version: int = 0x0200, feature_mask: int = 0x00000001) -> bytes:
    spec = pp.HandshakeSpec(
        proto='tron',
        proto_version=version,
        feature_mask=feature_mask,
        session_nonce=struct.pack('!I', 0xBEEFB07F),
        peer_seed=hashlib.sha256(struct.pack('!III', 0xDEADBEEF, version, feature_mask)).digest()[:32],
    )
    return spec.encode()


def parse_peer_response(buf: bytes) -> dict:
    items = pp.decode_tlv_stream(buf)
    out = {}
    for t, v in items:
        if t == pp.TLV_TYPE_PROTO_VERSION:
            out['proto_version'] = int.from_bytes(v[:2], 'big')
        elif t == pp.TLV_TYPE_BADGE:
            out['badge_present'] = True
        elif t == pp.TLV_TYPE_PAYLOAD:
            out['payload_len'] = len(v)
    return out


def main() -> int:
    global PORT
    if len(sys.argv) > 1:
        PORT = int(sys.argv[1])
    print(f"Checking seednode at {HOST}:{PORT}")
    print('Resolved port via env/token, using actual runtime port:', PORT)
    handshake = build_handshake()
    ts = time.time()
    with socket.create_connection((HOST, PORT), timeout=TIMEOUT) as s:
        s.settimeout(TIMEOUT)
        s.sendall(handshake)
        peer = s.recv(4096)
    dur = time.time() - ts
    print(f"handshake,target={HOST}:{PORT},sent={len(handshake)},received={len(peer)},duration_ms={int(dur*1000)}")
    if not peer:
        print('peer-response-missing')
        return 1
    print('peer-response-present')
    info = parse_peer_response(peer)
    print('peer-info=%s' % str(info))
    if info.get('proto_version') and info.get('badge_present'):
        print('status=SEEDHANDSHAKE-MATCH')
        return 0
    print('status=SEEDHANDSHAKE-STANDBY')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
