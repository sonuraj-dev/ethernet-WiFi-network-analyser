# Measurement Methodology

## Currently supported by the UDP test

- Sent and received request counts
- Packet-loss percentage
- Minimum, average and maximum RTT
- P95 RTT
- Jitter estimate based on consecutive successful RTT samples
- Per-packet sequence, timestamp, success state and error reason
- UDP payload rate when computed from successful payload bytes and elapsed time

## Metrics requiring additional work

| Metric | Additional requirement |
|---|---|
| One-way latency | Synchronized clocks or hardware timestamping |
| Physical bandwidth | Link negotiation details or a suitable capacity test |
| Bandwidth utilization | Measured traffic rate plus reliable link capacity |
| TCP retransmissions | TCP traffic and operating-system counters or packet capture |
| Out-of-order packets | Receiver sequence analysis or packet capture |
| Frame/CRC errors | Supported NIC/PHY counters or managed-device telemetry |
| Collisions | Hardware/driver counters where applicable |
| TTL expiry | Traceroute or purpose-built TTL-limited probes |
| Availability/uptime | Repeated monitoring over a documented time window |
| Server processing time | Responder-side timestamps and instrumentation |

Do not label UDP echo RTT as one-way latency. Do not label application payload rate as maximum physical bandwidth.

## Suggested validation procedure

1. Test Ethernet alone.
2. Test Wi-Fi alone.
3. Test both endpoints concurrently.
4. Repeat each scenario several times with the same parameters.
5. Compare packet counts and saved experiment records.
6. Document environmental factors, timeouts and failures.
7. Preserve raw CSV results alongside any summarized report, after reviewing privacy.
