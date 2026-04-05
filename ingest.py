from dataclasses import dataclass
from datetime import datetime
import socket
import threading
import re
import shlex


@dataclass
class SyslogEntry:
    severity:str
    timestamp:datetime
    hostname:str
    daemon:str
    message:str


def ingest(syslog_entries, conn):
    # Supports up to 200,000 KB (204,800,000 bytes)
    MAX_INGEST_BYTES = 200000 * 1024
    CHUNK_SIZE = 65536

    raw_buffer = bytearray(data.encode("utf-8", errors="replace"))

    # Continue reading remaining payload chunks for large ingest bodies
    conn.settimeout(0.2)
    try:
        while len(raw_buffer) < MAX_INGEST_BYTES:
            chunk = conn.recv(min(CHUNK_SIZE, MAX_INGEST_BYTES - len(raw_buffer)))
            if not chunk:
                break
            raw_buffer.extend(chunk)
    except socket.timeout:
        pass
    finally:
        conn.settimeout(None)

    if len(raw_buffer) >= MAX_INGEST_BYTES:
        response = f"Payload too large. Max allowed is {MAX_INGEST_BYTES} bytes."
    else:
        full_data = raw_buffer.decode("utf-8", errors="replace")
        header, _, file_text = full_data.partition("\n")
        parts = header.strip().split()

        if len(parts) != 3:
            response = "Correct Usage: INGEST <file_path> <server_ip:port> + newline + file content"
        else:
            target = parts[2]
            try:
                server_ip, server_port_raw = target.rsplit(":", 1)
                server_port = int(server_port_raw)
            except ValueError:
                response = "Invalid target. Use <server_ip:port>."
            else:
                pattern = re.compile(
                    r'^(?P<month>\w{3})\s+(?P<day>\d{1,2})\s+(?P<time>\d{2}:\d{2}:\d{2})\s+'
                    r'(?P<host>\S+)\s+(?P<service>[^\[:]+)(?:\[(?P<pid>\d+)\])?:\s(?P<message>.*)$'
                )

                parsed_logs = []
                for line in file_text.splitlines():
                    match = pattern.match(line)
                    if match:
                        parsed_logs.append(match.groupdict())


                current_year = datetime.now().year

                for item in parsed_logs:
                    ts = datetime.strptime(
                        f"{item['month']} {item['day']} {item['time']}",
                        "%b %d %H:%M:%S"
                    ).replace(year=current_year)

                    msg = item.get("message", "")
                    msg_l = msg.lower()
                    if "critical" in msg_l or "fatal" in msg_l:
                        sev = "CRITICAL"
                    elif "error" in msg_l or "fail" in msg_l:
                        sev = "ERROR"
                    elif "warn" in msg_l:
                        sev = "WARNING"
                    elif "debug" in msg_l:
                        sev = "DEBUG"
                    else:
                        sev = "INFO"

                    syslog_entries.append(
                        SyslogEntry(
                            severity=sev,
                            timestamp=ts,
                            hostname=item["host"],
                            daemon=item["service"].strip(),
                            message=msg
                        )
                    )
                    
                response = (
                    f"INGEST complete for {server_ip}:{server_port}. "
                    f"Parsed {len(parsed_logs)} log line(s)."
                )