import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st
import pandas as pd
import plotly.express as px
from storage import init_db, save_run, get_runs, get_packets, export_run_csv
from network_tests import run_udp_test, probe_udp
from serial_console import read_serial

ROOT = Path(__file__).resolve().parents[1]
init_db()

st.set_page_config(page_title="Ethernet Network Analyser",
                   page_icon="📡", layout="wide")
st.title("📡 Ethernet Network Analyser")
st.caption("Local dashboard • UDP echo measurements • SQLite history • CSV export")



with st.sidebar:
    st.header("Dashboard theme")
    theme_choice = st.radio(
        "Choose appearance",
        ["Theme 1 · Classic", "Theme 2 · Network Operations Center"],
        index=1,
        key="dashboard_theme",
        label_visibility="collapsed"
    )
    st.divider()
    st.header("Network endpoints")
    eth_host = st.text_input("Ethernet ESP32 IP", "172.16.15.50")
    eth_port = st.number_input("Ethernet UDP port", 1, 65535, 4210)
    wifi_host = st.text_input("Wi-Fi ESP32 IP", "10.218.72.197")
    wifi_port = st.number_input("Wi-Fi UDP port", 1, 65535, 4210)
    st.divider()
    st.subheader("USB serial ports")
    eth_serial = st.text_input("W5500 ESP32 serial", "/dev/ttyUSB1")
    wifi_serial = st.text_input("Wi-Fi ESP32 serial", "/dev/ttyUSB0")
    st.caption("Serial access is exclusive. Close PlatformIO Serial Monitor first.")

if theme_choice == "Theme 2 · Network Operations Center":
    st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] {
        background: #0b1220;
    }
    [data-testid="stHeader"] {
        background: rgba(11,18,32,.94);
    }
    [data-testid="stSidebar"] {
        background: #111827;
    }
    [data-testid="stMetric"] {
        background: #172235;
        border: 1px solid #29374b;
        border-radius: 12px;
        padding: 12px;
    }
    [data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 12px;
    }
    h1, h2, h3, p, label {
        letter-spacing: .01em;
    }
    </style>
    """, unsafe_allow_html=True)
    st.caption("NETWORK OPERATIONS CENTER  /  LIVE TELEMETRY")

tabs = st.tabs(["Live tests", "Packet history", "Serial consoles", "Firmware & files"])

with tabs[0]:
    st.subheader("Run an experiment")
    with st.form("test_form"):
        c1, c2 = st.columns(2)
        with c1:
            endpoint = st.selectbox("Test target", ["Ethernet", "Wi-Fi", "Both"])
            name = st.text_input("Experiment name", "Baseline UDP test")
            count = st.slider("Packets per endpoint", 5, 200, 30, 5)
            interval = st.slider("Interval (ms)", 0, 2000, 250, 50)
        with c2:
            timeout = st.slider("Reply timeout (ms)", 50, 5000, 1000, 50)
            payload = st.slider("Payload size (bytes)", 8, 200, 32, 8)
            notes = st.text_area("Experiment notes", "")
        submitted = st.form_submit_button("▶ Run test", type="primary")

    if submitted:
        from concurrent.futures import ThreadPoolExecutor, as_completed
        from queue import Queue, Empty
        import time

        targets = []
        if endpoint in ("Ethernet", "Both"):
            targets.append(("Ethernet", eth_host.strip(), int(eth_port), eth_serial))
        if endpoint in ("Wi-Fi", "Both"):
            targets.append(("Wi-Fi", wifi_host.strip(), int(wifi_port), wifi_serial))

        # Validate all selected endpoints before starting.
        ready = True
        for label, host, port, serial_port in targets:
            if not host:
                st.error(f"{label}: enter a valid IP address.")
                ready = False
            elif not os.path.exists(serial_port):
                st.error(f"{label}: configured serial device {serial_port} was not found.")
                ready = False
            elif not probe_udp(host, port, timeout_ms=1000):
                st.error(f"{label}: no UDP echo reply from {host}:{port}. Check the responder and network.")
                ready = False

        if ready:
            st.subheader("Live experiment")
            st.caption("Both endpoints run concurrently. Values update as packet replies arrive.")

            live_ui = {}
            top_cols = st.columns(len(targets))
            for col, (label, host, port, _) in zip(top_cols, targets):
                with col:
                    st.markdown(f"### {label}")
                    st.caption(f"{host}:{port}")
                    live_ui[label] = {
                        "progress": st.progress(0),
                        "status": st.empty(),
                        "metrics": st.empty(),
                        "chart": st.empty()
                    }
                    live_ui[label]["status"].info("Waiting for first packet...")
                    live_ui[label]["metrics"].markdown(
                        "**Sent:** 0  ·  **Received:** 0  ·  **Loss:** —"
                    )

            events = Queue()
            outcomes = {}
            failures = {}

            def measure(label, host, port):
                def update(snapshot):
                    events.put((label, snapshot))
                return run_udp_test(
                    host, port, count, interval, timeout, payload,
                    on_update=update
                )

            def render_live(label, snapshot):
                ui = live_ui[label]
                sent = snapshot["sent"]
                ui["progress"].progress(min(1.0, sent / count))
                ui["status"].markdown(
                    f"**Packet {sent}/{count}** · {snapshot['received']} replies"
                )
                def fmt(value, suffix=" ms"):
                    return f"{value}{suffix}" if value is not None else "—"
                ui["metrics"].markdown(
                    f"**Sent:** {sent}/{count}  ·  "
                    f"**Received:** {snapshot['received']}  ·  "
                    f"**Loss:** {snapshot['loss_pct']}%  \n\n"
                    f"**Avg RTT:** {fmt(snapshot['avg_ms'])}  ·  "
                    f"**Min:** {fmt(snapshot['min_ms'])}  ·  "
                    f"**Max:** {fmt(snapshot['max_ms'])}  ·  "
                    f"**Jitter estimate:** {fmt(snapshot['jitter_ms'])}  \n\n"
                    f"**UDP payload rate:** {fmt(snapshot['throughput_bps'], ' bit/s')}"
                )
                df = pd.DataFrame(snapshot["rows"])
                if not df.empty:
                    df["RTT (ms)"] = pd.to_numeric(df["rtt_ms"], errors="coerce")
                    valid = df[df["success"].astype(bool)]
                    if not valid.empty:
                        fig = px.area(
                            valid, x="sequence", y="RTT (ms)",
                            title=f"{label} · Live round-trip latency",
                            markers=True
                        )
                        fig.update_traces(line_color="#22c55e", fillcolor="rgba(34,197,94,0.22)")
                        fig.update_layout(
                            template="plotly_dark" if theme_choice.startswith("Theme 2") else "plotly_white",
                            height=280,
                            margin=dict(l=10, r=10, t=45, b=10),
                            xaxis_title="Packet sequence",
                            yaxis_title="RTT (ms)"
                        )
                        ui["chart"].plotly_chart(fig, width="stretch")

            with ThreadPoolExecutor(max_workers=len(targets)) as pool:
                future_map = {
                    pool.submit(measure, label, host, port): (label, host, port)
                    for label, host, port, _ in targets
                }
                pending = set(future_map)
                while pending:
                    try:
                        label, snapshot = events.get(timeout=0.10)
                        render_live(label, snapshot)
                    except Empty:
                        pass

                    for future in list(pending):
                        if future.done():
                            label, host, port = future_map[future]
                            try:
                                rows, metrics = future.result()
                                outcomes[label] = (host, port, rows, metrics)
                            except Exception as exc:
                                failures[label] = str(exc)
                                live_ui[label]["status"].error(f"Test failed: {exc}")
                            pending.remove(future)

                while not events.empty():
                    label, snapshot = events.get()
                    render_live(label, snapshot)

            # Persist each completed endpoint as a separate experiment.
            comparison_rows = []
            combined_frames = []
            for label, (host, port, rows, metrics) in outcomes.items():
                config = {
                    "name": name, "endpoint": label, "host": host,
                    "port": port, "count": count, "interval_ms": interval,
                    "timeout_ms": timeout, "payload_size": payload, "notes": notes
                }
                run_id = save_run(config, rows, metrics)
                frame = pd.DataFrame(rows)
                frame["endpoint"] = label
                frame["run_id"] = run_id
                frame["RTT (ms)"] = pd.to_numeric(frame["rtt_ms"], errors="coerce")
                combined_frames.append(frame)
                live_ui[label]["progress"].progress(1.0)
                live_ui[label]["status"].success(f"Completed · Saved experiment #{run_id}")

                st.session_state["last_run_id"] = run_id
                st.session_state["last_packet_rows"] = rows
                st.session_state["last_metrics"] = metrics
                st.session_state["last_endpoint"] = label

                comparison_rows.append({
                    "Endpoint": label,
                    "Experiment ID": run_id,
                    "Sent": metrics.get("sent"),
                    "Received": metrics.get("received"),
                    "Packet loss (%)": metrics.get("loss_pct"),
                    "Min RTT (ms)": metrics.get("min_ms"),
                    "Average RTT (ms)": metrics.get("avg_ms"),
                    "Max RTT (ms)": metrics.get("max_ms"),
                    "P95 RTT (ms)": metrics.get("p95_ms"),
                    "Jitter estimate (ms)": metrics.get("jitter_ms")
                })

            for label, message in failures.items():
                st.error(f"{label} test failed: {message}")

            # Full report appears below the live panels.
            if comparison_rows:
                st.divider()
                st.header("Completed experiment report")
                st.subheader("Ethernet vs Wi-Fi comparison")
                comparison = pd.DataFrame(comparison_rows).set_index("Endpoint")
                st.dataframe(comparison, width="stretch")
                st.download_button(
                    "Download comparison CSV",
                    comparison.reset_index().to_csv(index=False).encode("utf-8"),
                    file_name="ethernet_wifi_comparison.csv",
                    mime="text/csv", key="comparison_csv"
                )

                if combined_frames:
                    packets = pd.concat(combined_frames, ignore_index=True)
                    valid = packets[packets["success"].astype(bool)].copy()
                    if not valid.empty:
                        fig = px.line(
                            valid, x="sequence", y="RTT (ms)", color="endpoint",
                            markers=True, title="Final latency comparison",
                            labels={"sequence": "Packet sequence", "RTT (ms)": "RTT (ms)"}
                        )
                        fig.update_layout(
                            template="plotly_dark" if theme_choice.startswith("Theme 2") else "plotly_white",
                            height=420, hovermode="x unified"
                        )
                        st.plotly_chart(fig, width="stretch", key="final_comparison")
                    st.subheader("Complete packet-level results")
                    st.dataframe(packets, width="stretch")
                    st.download_button(
                        "Download combined packet CSV",
                        packets.to_csv(index=False).encode("utf-8"),
                        file_name="ethernet_wifi_combined_packets.csv",
                        mime="text/csv", key="combined_packets_csv"
                    )

                st.subheader("Metric interpretation")
                st.markdown(
                    "- **RTT:** measured request-to-echo round-trip time.\n"
                    "- **Jitter estimate:** mean absolute difference between consecutive successful RTT samples.\n"
                    "- **UDP payload rate:** successful payload bits divided by elapsed test time; not the physical link's maximum bandwidth.\n"
                    "- **One-way latency, TCP retransmissions, frame errors, collisions and TTL expiry:** not measured by this UDP echo test."
                )
                st.caption("Concurrent tests include laptop scheduling and network load. Results are practical comparisons, not a controlled physical-layer benchmark.")
            elif not failures:
                st.warning("No results were returned.")

    st.info("RTT is measured from the laptop to the UDP echo responder and back. Results include laptop, OS, Wi-Fi, and firmware effects; they are not a pure cable-only measurement.")

with tabs[1]:
    st.subheader("Saved experiment history")
    runs = get_runs()
    if runs.empty:
        st.info("No experiments saved yet. Run a test in Live tests.")
    else:
        st.dataframe(runs, width="stretch", hide_index=True)
        options = {f'#{r.id} · {r.endpoint} · {r.name} · {r.started_at}': int(r.id)
                   for r in runs.itertuples()}
        chosen = st.selectbox("Inspect an experiment", list(options))
        run_id = options[chosen]
        packets = get_packets(run_id)
        st.dataframe(packets, width="stretch", hide_index=True)
        st.download_button("Export selected run as CSV",
                           export_run_csv(run_id),
                           file_name=f"experiment_{run_id}.csv",
                           mime="text/csv")
        valid = packets[packets["success"] == 1].copy()
        if not valid.empty:
            valid["rtt_ms"] = pd.to_numeric(valid["rtt_ms"], errors="coerce")
            st.plotly_chart(px.scatter(valid, x="sequence", y="rtt_ms",
                                       title="Historical packet RTT",
                                       labels={"rtt_ms": "RTT (ms)"}),
                            width="stretch")
        st.download_button("Export all experiment summaries",
                           runs.to_csv(index=False).encode("utf-8"),
                           file_name="experiment_summaries.csv",
                           mime="text/csv")

with tabs[2]:
    st.subheader("Serial consoles")
    st.warning("A serial port can only be owned by one program at a time. Close PlatformIO's monitor before reading here. This reader opens the port briefly and closes it after capture.")
    c1, c2 = st.columns(2)
    for col, label, port in [
        (c1, "W5500 Ethernet ESP32", eth_serial),
        (c2, "Wi-Fi ESP32", wifi_serial)
    ]:
        with col:
            st.markdown(f"### {label}")
            st.code(port)
            if st.button(f"Capture recent serial output — {label}", key=f"serial_{label}"):
                try:
                    lines = read_serial(port, seconds=1.5)
                    st.session_state[f"serial_output_{label}"] = "\n".join(lines) or "(No lines received during capture.)"
                except Exception as exc:
                    st.session_state[f"serial_output_{label}"] = f"Serial error: {exc}"
            output = st.session_state.get(f"serial_output_{label}", "Click capture to read serial output.")
            st.text_area(f"{label} output", output, height=260, key=f"output_area_{label}")
            st.download_button(f"Save {label} output",
                               output.encode("utf-8"),
                               file_name=f"{label.lower().replace(' ', '_')}_serial.log",
                               mime="text/plain", key=f"save_serial_{label}")

with tabs[3]:
    st.subheader("Firmware history and project files")
    st.write("Baseline commit: `ed5d4ef` — working W5500 UDP responder.")
    st.write("Firmware snapshot: `firmware_history/v1_w5500_udp_responder.cpp`")
    st.write("Metadata: `firmware_history/v1_metadata.txt`")
    st.code("~/.platformio/penv/bin/pio run", language="bash")
    st.caption("Build only; it does not upload firmware.")
    history = ROOT / "firmware_history"
    for path in sorted(history.glob("*")):
        if path.is_file():
            st.write(f"**{path.name}** · {path.stat().st_size} bytes")
            if path.suffix in (".cpp", ".txt"):
                st.download_button(f"Download {path.name}",
                    path.read_bytes(), file_name=path.name,
                    key=f"fw_{path.name}")
    st.markdown("### Git history")
    import subprocess
    try:
        log = subprocess.run(
            ["git", "-C", str(ROOT), "log", "--oneline", "-15"],
            capture_output=True, text=True, timeout=3, check=True
        )
        st.code(log.stdout or "(No commits yet)")
    except Exception as exc:
        st.caption(f"Unable to read Git history: {exc}")

st.divider()
st.caption("Local-only prototype. Wi-Fi provisioning, automatic continuous polling, and firmware uploads are not enabled yet.")
