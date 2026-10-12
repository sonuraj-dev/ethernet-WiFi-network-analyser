from dashboard.network_tests import run_udp_test

def test_unreachable_endpoint_records_packet_loss():
    rows, metrics = run_udp_test(
        "127.0.0.1", port=1, count=2,
        interval_ms=0, timeout_ms=80, payload_size=8
    )
    assert len(rows) == 2
    assert metrics["sent"] == 2
    assert metrics["received"] == 0
    assert metrics["loss_pct"] == 100.0
