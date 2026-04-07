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
import shlex

def run_client(cmd, HOST, PORT):
 
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((HOST, PORT))
        client.send(cmd.encode())
        print("Connected to server, Server working...")
        response = client.recv(4096).decode()
        print("============================================================")
        print("Server response:\n", response)
    except ConnectionRefusedError:
        print(f"Cannot connect to {HOST}:{PORT}")
    except OSError as e:
        print(f"Socket error: {e}")
    finally:
        client.close()

def start_client():

    print("Welcome")
    print("Type 'HELP' to see available commands")

    while True:
        cmd = input("Enter command: ")
        parts = cmd.split()

        if len(parts) == 3 and parts[0] == "INGEST":
            server = parts[2]
            file_path = parts[1]
            try:
                server_ip, server_port = server.split(":")
                server_port = int(server_port)
            except ValueError:
                print("Invalid server format. Use <IP>:<PORT>")
                continue   

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
            try:
                server_ip, server_port = server.split(":")
                server_port = int(server_port)
            except ValueError:
                print("Invalid server format. Use <IP>:<PORT>")
                continue   
            run_client(cmd, server_ip, server_port)

        elif len(parts) >= 4 and parts[0] == "QUERY":
            try:
                qparts = shlex.split(cmd.strip())
            except ValueError:
                print("Invalid QUERY syntax.")
                continue

            if len(qparts) < 4:
                print(
                    "Correct Usage: QUERY <IP_or_DNS>:<Port> "
                    "<SEARCH_DATE|SEARCH_HOST|SEARCH_DAEMON|SEARCH_SEVERITY|SEARCH_KEYWORD|COUNT_KEYWORD> <value>"
                )
                continue

            target = qparts[1]
            qtype = qparts[2].upper()
            valid_qtypes = {
                "SEARCH_DATE",
                "SEARCH_HOST",
                "SEARCH_DAEMON",
                "SEARCH_SEVERITY",
                "SEARCH_KEYWORD",
                "COUNT_KEYWORD",
            }
            if qtype == 'SEARCH_DATE':
                print("working")
                qvalue = " ".join(qparts[3:]).strip('"')
                print(f"data = {qvalue}")

            try:
                server_ip, server_port = server.split(":")
                server_port = int(server_port)
            except ValueError:
                print("Invalid server format. Use <IP>:<PORT>")
                continue   

            if qtype not in valid_qtypes:
                print(
                    f"Unknown QUERY type: {qtype}. "
                    "Use SEARCH_DATE, SEARCH_HOST, SEARCH_DAEMON, SEARCH_SEVERITY, SEARCH_KEYWORD, or COUNT_KEYWORD."
                )
                continue

     


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
                print("QUERY <SERVER_IP>:<SERVER_PORT> <SEARCH_DATE|SEARCH_HOST|SEARCH_DAEMON|SEARCH_SEVERITY|SEARCH_KEYWORD|COUNT_KEYWORD> <value>")
                print("Usage: Query log files on the server")
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

        else:
            print(f"Unknown command: {cmd}, type 'HELP' for available commands.")
        






