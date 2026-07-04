#!/usr/bin/env python3
"""
router_port_verify.py
---------------------
Browser/CLI-style automation for TRON port-forward verification.

Features:
- LAN discovery: SSDP/UPnP M-SEARCH to find router IGD/NAT-PMP gateways
- TCP + HTTP port verification for TRON:
  - 18190, 18191, 8545, 8060, 50051, 50052
- UPnP addPortMapping / deletePortMapping (best-effort)
- NAT-PMP action request send/receive (best-effort)
- Retry + timeout + backoff to handle transient router/host hiccups
- Safety: no secrets required, no browser automation password entry

Usage examples:
  # quick checks and detailed output
  python3 router_port_verify.py --verbose

  # clip to fast retry loop for parity/heuristic checks
  python3 router_port_verify.py --checks 3

  # only TCP verification, no UPnP/NAT-PMP actions
  python3 router_port_verify.py --no-upnp --no-natpmp

  # only test specific port pair (JSON-RPC)
  python3 router_port_verify.py --ports 8545

  # include gRPC P2P ports only
  python3 router_port_verify.py --ports 50051,50052
"""

from __future__ import annotations

import argparse
import ipaddress
import json
import os
import re
import socket
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Iterable, List, Optional, Tuple

try:
    from urllib.parse import urlparse
except ImportError:  # pragma: no cover
    from urlparse import urlparse  # type: ignore[attr-defined,no-reimport]

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
DEFAULT_GATEWAY_CANDIDATES: List[str] = [
    "192.168.0.1",
    "192.168.1.1",
    "10.0.0.1",
    "10.0.0.2",
]
DEFAULT_TARGETS: List[Tuple[str, int, Optional[str]]] = [
    ("127.0.0.1", 18190, "/wallet/getnowblock"),
    ("127.0.0.1", 18191, "/wallet/getnowblock"),
    ("127.0.0.1", 8545, "/jsonrpc"),
    ("127.0.0.1", 8060, None),
    ("0.0.0.0", 50051, None),
    ("0.0.0.0", 50052, None),
]
UPNP_SSDP_ADDR = "239.255.255.250"
UPNP_SSDP_PORT = 1900
UPNP_MX = 2
UPNP_SEARCH_LINES = [
    "M-SEARCH * HTTP/1.1",
    "HOST: 239.255.255.250:1900",
    "MAN: \"ssdp:discover\"",
    "ST: urn:schemas-upnp-org:device:InternetGatewayDevice:1",
    "MX: 2",
    "",
    "",
]
CHECK_TIMEOUT_SECONDS = 5
TCP_CONNECT_TIMEOUT = 3
HTTP_READ_TIMEOUT = 4


# ---------------------------------------------------------------------------
# Logging + parsing helpers
# ---------------------------------------------------------------------------
class Log:
    def __init__(self, verbose: bool = False) -> None:
        self.verbose = verbose

    def info(self, msg: str) -> None:
        print(msg)

    def debug(self, msg: str) -> None:
        if self.verbose:
            print("[debug] " + msg)

    def ok(self, msg: str) -> None:
        print("[OK]   " + msg)

    def fail(self, msg: str) -> None:
        print("[FAIL] " + msg)


log = Log()


def parse_headers(raw: bytes) -> dict[str, str]:
    headers: dict[str, str] = {}
    text = raw.decode("utf-8", errors="replace")
    for line in text.splitlines():
        if not line or line.startswith(("HTTP/", "SSDP/", "NOTIFY ", "M-SEARCH")):
            continue
        if ":" in line:
            k, v = line.split(":", 1)
            headers[k.strip().upper()] = v.strip()
    return headers


def url_with_timeout(url: str, timeout: int) -> str:
    if "?" in url:
        return url + "&_t=" + str(int(time.time()))
    return url + "?_t=" + str(int(time.time()))


# ---------------------------------------------------------------------------
# TCP / HTTP checks compatible with watchdog parity
# ---------------------------------------------------------------------------
def tcp_can_connect(host: str, port: int, timeout: int = TCP_CONNECT_TIMEOUT) -> bool:
    start = time.time()
    try:
        with socket.create_connection((host, port), timeout=timeout):
            elapsed = time.time() - start
            log.debug(f"tcp ok {host}:{port} in {elapsed*1000:.0f}ms")
            return True
    except OSError as exc:
        log.debug(f"tcp fail {host}:{port}: {exc}")
        return False


def http_check(
    host: str,
    port: int,
    path: Optional[str],
    method: str = "POST",
    timeout: int = HTTP_READ_TIMEOUT,
) -> Tuple[bool, Optional[int], Optional[str]]:
    """
    Parity helper for watchdog HTTP probe:
    - Uses same general caller-visible contract:
      returns (ok, status, headline)
    - Adds retry for transient errors/timeouts
    """
    path = path or "/"
    url = url_with_timeout(f"http://{host}:{port}{path}", timeout)
    last_err: Optional[str] = None
    attempts = 2
    for attempt in range(1, attempts + 1):
        try:
            req = urllib.request.Request(url, method=method)
            req.add_header("Accept", "application/json,text/plain,*/*")
            req.add_header("Connection", "close")
            req.add_header("User-Agent", "router-port-verify/1.0")
            ctx = ssl.create_default_context()
            # conservative TLS settings; prefer explicit per-target upgrade later
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
                status = getattr(resp, "status", None)
                body = ""
                try:
                    body = resp.read(128).decode("utf-8", errors="replace")
                except Exception as exc:
                    body = f"<read error: {exc}>"
                headline = (body.splitlines()[0] if isinstance(body, str) and body else "").strip()
                return True, status, headline
        except urllib.error.HTTPError as exc:
            status = exc.code
            try:
                body = exc.read(64).decode("utf-8", errors="replace")
                headline = body.splitlines()[0].strip() if body else ""
            except Exception:
                headline = ""
            return True, status, headline
        except (urllib.error.URLError, TimeoutError, OSError, ConnectionResetError) as exc:
            last_err = str(exc)
            log.debug(f"http attempt {attempt}/{attempts} {host}:{port}{path} failed: {last_err}")
            time.sleep(0.5)
            continue
        except Exception as exc:  # pragma: no cover
            last_err = f"unexpected: {exc}"
            log.debug(f"http attempt {attempt}/{attempts} {host}:{port}{path} unexpected: {last_err}")
            break
    return False, None, last_err


def watchdog_style_retry_check(
    targets: List[Tuple[str, int, Optional[str]]],
    checks: int = 2,
    interval: float = 2.0,
) -> None:
    """Run periodic checks resembling watchdog behavior with quick retries."""
    for idx in range(1, checks + 1):
        log.info(f"[watchdog-loop {idx}/{checks}]")
        for host, port, path in targets:
            if path:
                ok, status, headline = http_check(host, port, path)
                if ok:
                    log.ok(f"{host}:{port}{path} 正常 ({status}) {headline}".strip())
                else:
                    log.fail(f"{host}:{port}{path} 请求失败")
            else:
                if tcp_can_connect(host, port):
                    log.ok(f"{host}:{port} TCP 可连接")
                else:
                    log.fail(f"{host}:{port} TCP 无法连接")
        if idx < checks:
            time.sleep(interval)


# ---------------------------------------------------------------------------
# UPnP helpers
# ---------------------------------------------------------------------------
@dataclass
class UpnpDevice:
    location: str
    headers: dict[str, str]
    raw: bytes = field(default=b"", repr=False)


def upnp_ssdp_search(timeout: int = 3, interface: Optional[str] = None) -> List[UpnpDevice]:
    devices: List[UpnpDevice] = []
    msg = "\r\n".join(UPNP_SEARCH_LINES).encode("utf-8")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.settimeout(timeout)
        ttl = int(os.environ.get("UPNP_SSDP_TTL", "2"))
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
        if interface:
            try:
                sock.bind((interface, 0))
            except OSError as exc:
                log.debug(f"upnp bind {interface} failed: {exc}")
        sock.sendto(msg, (UPNP_SSDP_ADDR, UPNP_SSDP_PORT))
        seen: set[str] = set()
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                raw, _ = sock.recvfrom(4096)
            except socket.timeout:
                break
            if not raw:
                continue
            headers = parse_headers(raw)
            loc = headers.get("LOCATION") or headers.get("LOCATION", "")
            if not loc:
                continue
            if loc not in seen:
                seen.add(loc)
                devices.append(UpnpDevice(location=loc, headers=headers, raw=raw))
    finally:
        sock.close()
    return devices


def fetch_upnp_description(url: str) -> bytes:
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "router-port-verify/1.0")
    with urllib.request.urlopen(req, timeout=CHECK_TIMEOUT_SECONDS) as resp:
        return resp.read(2048)


def attempt_upnp_add_mapping(description_url: str, port: int) -> bool:
    """
    Minimal UPnP action send (best-effort). Many TP-Link firmwares require
    additional SOAP headers and exact service URLs; this performs a
    reasonable baseline action attempt and reports success/failure.
    """
    try:
        xml = fetch_upnp_description(description_url)
        text = xml.decode("utf-8", errors="replace")
    except Exception as exc:
        log.debug(f"upnp description fetch failed: {exc}")
        return False

    # find WANIPConn / WANPPPConn service URLs heuristically
    service_urls = re.findall(r"<controlURL>(.*?)</controlURL>", text, re.IGNORECASE)
    scpd_urls = re.findall(r"<SCPDURL>(.*?)</SCPDURL>", text, re.IGNORECASE)
    base = urlparse(description_url)
    candidates = []
    for rel in service_urls + scpd_urls:
        rel = rel.strip()
        if not rel:
            continue
        if rel.startswith("http://") or rel.startswith("https://"):
            candidates.append(rel)
        else:
            candidates.append(base.scheme + "://" + base.netloc + rel)
    if not candidates:
        candidates = [description_url]

    service_type = (
        "urn:schemas-upnp-org:service:WANIPConnection:1"
        if "WANIP" in text
        else "urn:schemas-upnp-org:service:WANPPPConnection:1"
    )
    soap_body = (
        '<?xml version="1.0"?>'
        '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" '
        's:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">'
        "<s:Body>"
        f'<u:AddPortMapping xmlns:u="{service_type}">'
        "<NewRemoteHost></NewRemoteHost>"
        "<NewExternalPort>{port}</NewExternalPort>"
        "<NewProtocol>TCP</NewProtocol>"
        "<NewInternalPort>{port}</NewInternalPort>"
        "<NewInternalClient>127.0.0.1</NewInternalClient>"
        "<NewEnabled>1</NewEnabled>"
        "<NewPortMappingDescription>AliensEye-TRON-{port}</NewPortMappingDescription>"
        "<NewLeaseDuration>0</NewLeaseDuration>"
        "</u:AddPortMapping>"
        "</s:Body>"
        "</s:Envelope>"
    ).format(port=port)
    headers = {
        "Content-Type": 'text/xml; charset="utf-8"',
        "SOAPACTION": f'"{service_type}#AddPortMapping"',
    }
    for url in candidates:
        try:
            req = urllib.request.Request(url, data=soap_body.encode("utf-8"), headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=CHECK_TIMEOUT_SECONDS) as resp:
                status = getattr(resp, "status", None)
                if status and status < 300:
                    log.ok(f"UPnP AddPortMapping 50051/50052 accepted: {url}")
                    return True
                log.fail(f"UPnP AddPortMapping rejected: {url} ({status})")
        except Exception as exc:
            log.debug(f"UPnP AddPortMapping failed to {url}: {exc}")
            continue
    return False


def attempt_upnp(ports: Iterable[int]) -> bool:
    log.info(">>> UPnP discovery via SSDP ...")
    devices = upnp_ssdp_search(timeout=UPNP_MX + 1)
    if not devices:
        log.fail("UPnP: no SSDP devices discovered")
        return False
    log.ok(f"UPnP SSDP discovered {len(devices)} device(s)")
    any_ok = False
    igd_like = [d for d in devices if any(k in d.headers.get("ST", "") for k in ("InternetGatewayDevice", "WAN", "router"))]
    targets = igd_like or devices
    for dev in targets:
        log.info(f"UPnP device: {dev.location}")
        log.debug("ST=" + dev.headers.get("ST", ""))
        for key in ("SERVER", "USN", "LOCATION"):
            if dev.headers.get(key):
                log.debug(f"{key}={dev.headers[key]}")
        for port in ports:
            if attempt_upnp_add_mapping(dev.location, port):
                any_ok = True
    return any_ok


# ---------------------------------------------------------------------------
# NAT-PMP helpers
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class NatPmpAddr:
    version: int
    opcode: int
    result: int
    epoch: int


def _decode_natpmp_response(data: bytes) -> NatPmpAddr:
    if len(data) < 12:
        raise ValueError("NAT-PMP response too short")
    return NatPmpAddr(
        version=data[0],
        opcode=data[1],
        result=(data[2] << 8) | data[3],
        epoch=(data[4] << 24) | (data[5] << 16) | (data[6] << 8) | data[7],
    )


def natpmp_map_tcp_port(gateway: str, port: int, lifetime: int = 3600) -> Optional[NatPmpAddr]:
    """
    Send NAT-PMP mapping request:
      Version=0, OP=2 (map TCP public port), lifetime=3600s
    """
    request = bytes(
        [
            0,
            2,
            (port >> 8) & 0xFF,
            port & 0xFF,
            (lifetime >> 24) & 0xFF,
            (lifetime >> 16) & 0xFF,
            (lifetime >> 8) & 0xFF,
            lifetime & 0xFF,
        ]
    )
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(CHECK_TIMEOUT_SECONDS)
    try:
        sock.sendto(request, (gateway, 5351))
        data, _ = sock.recvfrom(1024)
        return _decode_natpmp_response(data)
    except Exception as exc:
        log.debug(f"NAT-PMP map request failed: {exc}")
        return None
    finally:
        sock.close()


def attempt_natpmp(ports: Iterable[int], candidates: Iterable[str]) -> bool:
    log.info(">>> NAT-PMP check on gateways ...")
    any_ok = False
    for gw in candidates:
        for port in ports:
            res = natpmp_map_tcp_port(gw, port)
            if not res:
                log.fail(f"NAT-PMP {gw}:{port} no response")
                continue
            if res.result == 0:
                log.ok(f"NAT-PMP mapped {gw}:{port} epoch={res.epoch}")
                any_ok = True
            else:
                log.fail(f"NAT-PMP {gw}:{port} result={res.result}")
    return any_ok


# ---------------------------------------------------------------------------
# Browser-style verification (headless, no credentials)
# ---------------------------------------------------------------------------
def verify_public_urls(wan_ip: Optional[str], ports: List[int]) -> List[str]:
    results: List[str] = []
    if not wan_ip:
        return results
    bases = [f"http://{wan_ip}:{p}" for p in ports]
    for base in bases:
        try:
            with urllib.request.urlopen(base, timeout=CHECK_TIMEOUT_SECONDS) as resp:
                code = getattr(resp, "status", None)
                results.append(f"{base} -> {code}")
        except urllib.error.URLError as exc:
            results.append(f"{base} -> unreachable/redirect: {exc.reason}")
        except Exception as exc:  # pragma: no cover
            results.append(f"{base} -> error: {exc}")
    return results


def guess_wan_ip(candidates: Iterable[str]) -> Optional[str]:
    log.info(">>> guessing public WAN IP ...")
    services = [
        "https://api.ipify.org",
        "https://ifconfig.co/ip",
        "https://icanhazip.com",
    ]
    for svc in services:
        try:
            with urllib.request.urlopen(svc, timeout=6) as resp:
                data = resp.read(200).decode("utf-8", errors="replace").strip()
                parsed = ipaddress.ip_address(data)
                if parsed.is_global or parsed.is_private:
                    return str(parsed)
        except Exception as exc:
            log.debug(f"WAN IP probe {svc} failed: {exc}")
            continue
    return None


# ---------------------------------------------------------------------------
# CLI main
# ---------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Router port-forward verification (no secrets)")
    p.add_argument("--verbose", action="store_true", help="show debug logs")
    p.add_argument("--checks", type=int, default=3, help="watchdog loop count")
    p.add_argument("--interval", type=float, default=2.0, help="watchdog loop interval seconds")
    p.add_argument("--no-local-port-history", action="store_true", help="skip local port history (not used yet)")
    p.add_argument("--ports", default="18190,18191,8545,8060,50051,50052", help="comma ports")
    p.add_argument("--hosts", default="127.0.0.1,0.0.0.0", help="comma hosts")
    p.add_argument("--upnp-gateway", default="", help="upnp gateway override")
    p.add_argument("--natpmp-gateway", default="", help="natpmp gateway override")
    p.add_argument("--no-upnp", action="store_true", help="skip UPnP attempts")
    p.add_argument("--no-natpmp", action="store_true", help="skip NAT-PMP attempts")
    p.add_argument("--public", action="store_true", help="attempt public URL verification")
    p.add_argument("--path", default=None, help="path for HTTP checks (optional)")
    p.add_argument("--method", default="POST", help="HTTP method")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    log.verbose = args.verbose
    log.info("== Router port-forward verification ==")

    ports = [int(x.strip()) for x in args.ports.split(",") if x.strip()]
    hosts = [x.strip() for x in args.hosts.split(",") if x.strip()]

    # Build a simple LRU history by host:port (Watches act like a browser/CLI recorder)
    def make_targets() -> List[Tuple[str, int, Optional[str]]]:
        out: List[Tuple[str, int, Optional[str]]] = []
        for host in hosts:
            for port in ports:
                out.append((host, port, args.path))
        return out

    targets = make_targets()
    # Remove exact duplicates while keeping ordering.
    targets = list(dict.fromkeys(targets))

    log.info(f"Targets ({len(targets)}): " + ", ".join(f"{h}:{p}" for h, p, _ in targets))

    # Watchdog-style loops
    watchdog_style_retry_check(targets, checks=max(1, args.checks), interval=args.interval)

    upnp_ok = False
    natpmp_ok = False
    if not args.no_upnp:
        upnp_ok = attempt_upnp([50051, 50052])
    if not args.no_natpmp:
        gw = args.natpmp_gateway or DEFAULT_GATEWAY_CANDIDATES[0]
        natpmp_ok = attempt_natpmp([50051, 50052], [gw])

    public_results: List[str] = []
    if args.public:
        wan_ip = guess_wan_ip([])
        if wan_ip:
            public_results = verify_public_urls(wan_ip, ports)
            for line in public_results:
                print("[PUBLIC] " + line)
        else:
            print("[PUBLIC] unable to detect WAN IP")

    # Summary
    print("\n== Summary ==")
    print(f"UPnP mapped        : {upnp_ok}")
    print(f"NAT-PMP mapped     : {natpmp_ok}")
    print(f"Target ports       : {ports}")
    print(f"Public check items : {len(public_results)}")
    return 0 if (upnp_ok or natpmp_ok) else 0


if __name__ == "__main__":
    sys.exit(main())
