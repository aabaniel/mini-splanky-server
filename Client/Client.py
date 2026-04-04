'''
Uploading Logs: INGEST <file_path> <IP_or_DNS>:<Port>
Querying by Date: QUERY <IP_or_DNS>:<Port> SEARCH_DATE "<date_string>"
Querying by Host: QUERY <IP_or_DNS>:<Port> SEARCH_HOST <hostname>
Querying by Daemon: QUERY <IP_or_DNS>:<Port> SEARCH_DAEMON <daemon_name>
Querying by Severity: QUERY <IP_or_DNS>:<Port> SEARCH_SEVERITY <severity_level>
Keyword Search: QUERY <IP_or_DNS>:<Port> SEARCH_KEYWORD <keyword>
Keyword Count: QUERY <IP_or_DNS>:<Port> COUNT_KEYWORD <keyword>
Erasing Data: PURGE <IP_or_DNS>:<Port>
'''


# client.py
import socket

def run_client(cmd, HOST, PORT):
 
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((HOST, PORT))
        client.send(cmd.encode())
        response = client.recv(4096).decode()
        print("Server response:\n", response)
    except ConnectionRefusedError:
        print(f"Cannot connect to {HOST}:{PORT}")
    except OSError as e:
        print(f"Socket error: {e}")
    finally:
        client.close()

def start_client():

    print("Welcome, Use INGEST Or PURGE to connect to the server.")
    print("Type 'HELP' to see available commands")

    while True:
        cmd = input("Enter command: ")
        parts = cmd.split()

        if len(parts) == 3 and parts[0] == "INGEST":
            server = parts[2]
            server_ip, server_port = server.split(":")
            server_port = int(server_port)
            file_path = parts[1]

            try:
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    file_text = f.read()
            except FileNotFoundError:
                print(f"File not found: {file_path}")
                continue
            except OSError as e:
                print(f"Failed to read file: {e}")
                continue

            # Send command header + full file content as one payload
            cmd = f"{cmd}\n{file_text}"

            run_client(cmd, server_ip, server_port)

        elif len(parts) == 2 and parts[0] == "PURGE":
            server = parts[1]
            server_ip, server_port = server.split(":")
            server_port = int(server_port)
            run_client(cmd, server_ip, server_port)

        elif cmd == "HELP":
                print("List of Commands:")
                print("================================================")
                print("INGEST <FILE_PATH> <SERVER_IP>:<SERVER_PORT>")
                print("Usage: Read file path, and send to server for parsing")
                print("================================================")
                print("PURGE <SERVER_IP>:<SERVER_PORT>")
                print("Usage: Deletes log files from the server")
                print("================================================")
                print("HELP")
                print("Usage: Display all possible commands")
                print("================================================")
                print("EXIT")
                print("Usage: Close Program")
                print("================================================")


        elif cmd == "EXIT":
            print("Closing Program")
            break
        






