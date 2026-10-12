import socket
import time
import statistics
from datetime import datetime, timezone

def run_udp_test(host, port=4210, count=20, interval_ms=250,
                 timeout_ms=1000, payload_size=16, progress=None,
                 on_update=None):
    count = max(1, min(int(count), 500))
    payload_size = max(8, min(int(payload_size), 200))
    timeout_ms = max(50, min(int(timeout_ms), 10000))
    interval_ms = max(0, min(int(interval_ms), 10000))
    rows, rtts = [], []
    received = 0
    test_started = time.perf_counter()

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(timeout_ms / 1000)
        for seq in range(1, count + 1):
            token = f"ENA-{seq:06d}-{time.monotonic_ns()}".encode()
            payload = (token + b"X" * payload_size)[:payload_size]
            sent_at = datetime.now(timezone.utc).isoformat()
            start = time.perf_counter()
            error, rtt, success = "", None, False
            try:
                sock.sendto(payload, (host, int(port)))
                reply, address = sock.recvfrom(2048)
                elapsed = (time.perf_counter() - start) * 1000
                if address[0] != host:
                    error = f"Unexpected sender: {address[0]}"
                elif reply != payload:
                    error = "Reply payload did not match request"
                else:
                    rtt, success = round(elapsed, 3), True
                    received += 1
                    rtts.append(rtt)
            except socket.timeout:
                error = "Timeout"
            except OSError as exc:
                error = str(exc)

            rows.append({
                "sequence": seq,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "sent_at": sent_at,
                "rtt_ms": rtt,
                "success": success,
                "error": error
            })
            if progress:
                progress(seq / count, f"Packet {seq}/{count}")
            if on_update:
                elapsed_s = max(time.perf_counter() - test_started, 0.000001)
                on_update({
                    "rows": list(rows),
                    "sent": seq,
                    "received": received,
                    "loss_pct": round((seq - received) * 100 / seq, 2),
                    "avg_ms": round(statistics.mean(rtts), 3) if rtts else None,
                    "min_ms": round(min(rtts), 3) if rtts else None,
                    "max_ms": round(max(rtts), 3) if rtts else None,
                    "jitter_ms": round(statistics.mean(
                        [abs(b-a) for a, b in zip(rtts, rtts[1:])]
                    ), 3) if len(rtts) > 1 else None,
                    "throughput_bps": round(received * payload_size * 8 / elapsed_s, 2),
                })
            if seq < count and interval_ms:
                time.sleep(interval_ms / 1000)

    ordered = sorted(rtts)
    p95 = ordered[min(len(ordered)-1, int(0.95 * len(ordered)))] if ordered else None
    diffs = [abs(b-a) for a, b in zip(rtts, rtts[1:])]
    metrics = {
        "sent": count,
        "received": received,
        "loss_pct": round((count - received) * 100 / count, 2),
        "min_ms": round(min(rtts), 3) if rtts else None,
        "avg_ms": round(statistics.mean(rtts), 3) if rtts else None,
        "max_ms": round(max(rtts), 3) if rtts else None,
        "p95_ms": round(p95, 3) if p95 is not None else None,
        "jitter_ms": round(statistics.mean(diffs), 3) if diffs else None
    }
    return rows, metrics


def probe_udp(host, port=4210, timeout_ms=700):
    """Return True only when the expected UDP echo reply is received."""
    import socket
    import time
    token = f"ENA-PROBE-{time.monotonic_ns()}".encode()
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(max(0.1, timeout_ms / 1000))
            sock.sendto(token, (host, int(port)))
            reply, address = sock.recvfrom(512)
            return address[0] == host and reply == token
    except (OSError, socket.timeout):
        return False
