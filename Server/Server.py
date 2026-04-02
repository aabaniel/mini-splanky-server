import socket
import threading

HOST = '0.0.0.0'
PORT = 11017


connected_ips = []

from cmd import purge
import re

def handle_client(conn, addr):
    print(f"[CLIENT THREAD STARTED] {addr}")

    ip = addr[1]


    if ip not in connected_ips:
         connected_ips.append(ip)

    print(f"[CONNECTED] {addr}")
    print(f"[IP LIST] {connected_ips}")

    while True:
        try:
            data = conn.recv(1024).decode()

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
                

                elif command == "INGEST":
                    if len(cmd_parts) < 3:
                        response = "Correct Usage: INGEST <argument>"
                    else:
                        argument = " ".join(cmd_parts[1:])
                        response = f"INGESTED: {argument}"

                        header, _, file_text = data.partition("\n")
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
                        

   
                elif command == "PURGE":
                    purge()

     

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