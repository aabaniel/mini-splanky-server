from dataclasses import dataclass
from datetime import datetime
import socket
import threading

@dataclass
class SyslogEntry:
    severity:str
    timestamp:datetime
    hostname:str
    daemon:str
    message:str

#datetime basis "abbr. name  day of month  hour:minute:seconds" "%b %d %H:%M:%S"



HOST = '0.0.0.0'
PORT = 11017

global syslog_entries 
connected_ips = []
syslog_entries = []


import re
import shlex

ingest_semaphore = threading.Semaphore(1)
query_semaphore = threading.Semaphore(1)
purge_semaphore = threading.Semaphore(1)

@dataclass
class client:
    Client_IP: str
    Port_Used: int



def handle_client(conn, addr):
    print(f"[CLIENT THREAD STARTED] {addr}")

    ip = addr[0]


    if ip not in connected_ips:
         connected_ips.append(ip)

    print(f"[CONNECTED] {addr}")
    print(f"[CLIENT PORT LIST] {[addr[1]]}")

    while True:
        try:
            data = conn.recv(1024).decode() # controls total data gathered

            if not data:
                break
            cmd_parts = data.strip().split()

            if len(cmd_parts) == 0:
                response = "Empty command"

            else:
                command = cmd_parts[0]

                
                if command == "ping":
                    response = f"pong"

                elif command == "exit":
                    response = f"Goodbye!"
                    conn.send(response.encode())
                    break
                

###################################################################

                elif command == "INGEST":
                    
                    if not ingest_semaphore.acquire(blocking=False):
                        response = f"Server currently writing to memory, try again later. "
                        conn.send(response.encode())
                        break
                       

                   
                    try:
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
                    finally:
                        ingest_semaphore.release()
###################################################################
   
                elif command == "PURGE":

                    if not purge_semaphore.acquire(blocking=False):
                        response = f"Server currently being purged, try again later. "
                    else:
                        try:
                            count = len(syslog_entries)
                            if count == 0:
                                response = f"Nothing to purge, {count} log entries in server."
                            else:
                                syslog_entries.clear()
                                response = f"Server successfully purged, {count} log entries deleted."
                        finally:
                            purge_semaphore.release()

###################################################################

                elif command == "QUERY":

                    if not query_semaphore.acquire(blocking=False):
                        response = "Server currently handling another query, try again later."
                    else:
                        try:
                            try:
                                qparts = shlex.split(data.strip())
                            except ValueError:
                                response = "Invalid QUERY syntax."
                                qparts = []

                            if qparts:
                                # Expected:
                                # QUERY <IP_or_DNS>:<Port> <SEARCH_DATE|SEARCH_HOST|SEARCH_DAEMON|SEARCH_SEVERITY|SEARCH_KEYWORD|COUNT_KEYWORD> <value>
                                if len(qparts) < 4:
                                    response = (
                                        "Correct Usage: QUERY <IP_or_DNS>:<Port> "
                                        "<SEARCH_DATE|SEARCH_HOST|SEARCH_DAEMON|SEARCH_SEVERITY|SEARCH_KEYWORD|COUNT_KEYWORD> <value>"
                                    )
                                else:
                                    target = qparts[1]
                                    qtype = qparts[2].upper()
                                    qvalue = " ".join(qparts[3:]).strip()

                                    try:
                                        _, port_raw = target.rsplit(":", 1)
                                        int(port_raw)
                                    except ValueError:
                                        response = "Invalid target. Use <IP_or_DNS>:<Port>."
                                    if not syslog_entries:
                                        response = "No indexed log entries to query."
                                    else:
                                        def fmt_entry(e: SyslogEntry) -> str:
                                            ts = e.timestamp.strftime("%b %d %H:%M:%S")
                                            return f"{ts} {e.hostname} {e.daemon}: {e.message}"

                                        matches = []

                                        if qtype == "SEARCH_DATE":
                                            needle = qvalue.lower()
                                            for e in syslog_entries:
                                                ts = e.timestamp.strftime("%b %d %H:%M:%S").lower()
                                                if ts.startswith(needle):
                                                    matches.append(e)
                                            if matches:
                                                lines = [f"Found {len(matches)} matching entr{'y' if len(matches)==1 else 'ies'} for date '{qvalue}':"]
                                                lines += [f"{i}. {fmt_entry(e)}" for i, e in enumerate(matches, 1)]
                                                response = "\n".join(lines)
                                            else:
                                                response = f"No matching entries found for date '{qvalue}'."

                                        elif qtype == "SEARCH_HOST":
                                            for e in syslog_entries:
                                                if e.hostname.lower() == qvalue.lower():
                                                    matches.append(e)
                                            if matches:
                                                lines = [f"Found {len(matches)} matching entr{'y' if len(matches)==1 else 'ies'} for host '{qvalue}':"]
                                                lines += [f"{i}. {fmt_entry(e)}" for i, e in enumerate(matches, 1)]
                                                response = "\n".join(lines)
                                            else:
                                                response = f"No matching entries found for host '{qvalue}'."

                                        elif qtype == "SEARCH_DAEMON":
                                            for e in syslog_entries:
                                                if e.daemon.lower() == qvalue.lower():
                                                    matches.append(e)
                                            if matches:
                                                lines = [f"Found {len(matches)} matching entr{'y' if len(matches)==1 else 'ies'} for daemon '{qvalue}':"]
                                                lines += [f"{i}. {fmt_entry(e)}" for i, e in enumerate(matches, 1)]
                                                response = "\n".join(lines)
                                            else:
                                                response = f"No matching entries found for daemon '{qvalue}'."

                                        elif qtype == "SEARCH_SEVERITY":
                                            sev = qvalue.upper()
                                            for e in syslog_entries:
                                                if e.severity.upper() == sev:
                                                    matches.append(e)
                                            if matches:
                                                lines = [f"Found {len(matches)} matching entr{'y' if len(matches)==1 else 'ies'} for severity '{sev}':"]
                                                lines += [f"{i}. {fmt_entry(e)}" for i, e in enumerate(matches, 1)]
                                                response = "\n".join(lines)
                                            else:
                                                response = f"No matching entries found for severity '{sev}'."

                                        elif qtype == "SEARCH_KEYWORD":
                                            needle = qvalue.lower()
                                            for e in syslog_entries:
                                                if needle in e.message.lower():
                                                    matches.append(e)
                                            if matches:
                                                lines = [f"Found {len(matches)} matching entr{'y' if len(matches)==1 else 'ies'} for keyword '{qvalue}':"]
                                                lines += [f"{i}. {fmt_entry(e)}" for i, e in enumerate(matches, 1)]
                                                response = "\n".join(lines)
                                            else:
                                                response = f"No matching entries found for keyword '{qvalue}'."

                                        elif qtype == "COUNT_KEYWORD":
                                            needle = qvalue.lower()
                                            count = sum(1 for e in syslog_entries if needle in e.message.lower())
                                            response = f"The keyword '{qvalue}' appears in {count} indexed log entr{'y' if count==1 else 'ies'}."

                                        else:
                                            response = (
                                                f"Unknown QUERY type: {qtype}. "
                                                "Use SEARCH_DATE, SEARCH_HOST, SEARCH_DAEMON, SEARCH_SEVERITY, SEARCH_KEYWORD, or COUNT_KEYWORD."
                                            )
                        finally:
                            query_semaphore.release()

###################################################################

                else:
                    response = f"Unknown command: {command}"


            try:
                conn.send(response.encode())
            except OSError as e:
                if getattr(e, "winerror", None) in (10053, 10054):
                    print(f"[DISCONNECT] {addr}: {e}")
                    break
                raise


        except Exception as e:
            print(f"[ERROR] {addr}: {e}")
            break

    conn.close()
    print(f"[DISCONNECTED] {addr}")
    if ip in connected_ips:
        connected_ips.remove(ip)


def connection_handler(server):
    print("[ACCEPT THREAD STARTED]")

    while True:
        conn, addr = server.accept()

        global client_thread 
        client_thread = threading.Thread(target=handle_client,args=(conn, addr))
        client_thread.start() 
        client_thread.join()


def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)

    print(f"Server listening on {HOST}:{PORT}...")

    accept_thread = threading.Thread(
        target=connection_handler, 
        args=(server,)
    )
    accept_thread.start()

   
    while True:
        # You can put admin commands or monitoring here
        pass


start_server()
#INGEST SVR1_server_auth_syslog.txt IP:11017
#INGEST SVR2_server_auth_syslog.txt IP:11017