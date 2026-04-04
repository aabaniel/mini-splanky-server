from dataclasses import dataclass
import socket
import threading

HOST = '0.0.0.0'
PORT = 11017


connected_ips = []


import re

@dataclass
class client:
    Client_IP: str
    Port_Used: int



def handle_client(conn, addr):
    print(f"[CLIENT THREAD STARTED] {addr}")

    ip = addr[1]


    if ip not in connected_ips:
         connected_ips.append(ip)

    print(f"[CONNECTED] {addr}")
    print(f"[IP LIST] {connected_ips}")

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

                                response = (
                                    f"INGEST complete for {server_ip}:{server_port}. "
                                    f"Parsed {len(parsed_logs)} log line(s)."
                                )
                        
###################################################################
   
                elif command == "PURGE":
                    response = f"me when i purge"
                    conn.send(response.encode())
                    break

     

                else:
                    response = f"Unknown command: {command}"

            conn.send(response.encode())

        except Exception as e:
            print(f"[ERROR] {addr}: {e}")
            break

    conn.close()
    print(f"[DISCONNECTED] {addr}")


def connection_handler(server):
    print("[ACCEPT THREAD STARTED]")

    while True:
        conn, addr = server.accept()

        client_thread = threading.Thread(target=handle_client,args=(conn, addr))
        client_thread.start()


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