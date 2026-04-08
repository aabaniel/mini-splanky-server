###################################################################
# libraries 
###################################################################
from dataclasses import dataclass
from datetime import datetime
import socket
import threading
import re
import shlex

from Server.ingest import ingest
from Server.purge import purge
from Server.query import query

###################################################################
# dataclass initialization
###################################################################
@dataclass
class SyslogEntry:
    severity:str
    timestamp:datetime
    hostname:str
    daemon:str
    message:str
#datetime basis "abbr. name  day of month  hour:minute:seconds" "%b %d %H:%M:%S"

@dataclass
class client:
    Client_IP: str
    Port_Used: int

###################################################################
# initialization variables
###################################################################

HOST = '0.0.0.0'
PORT = 11017

global syslog_entries 
connected_ips = []
syslog_entries = []

write_semaphore = threading.Semaphore(1)
query_semaphore = threading.Semaphore(1)


###################################################################
# complete client function
###################################################################
def handle_client(conn, addr):
    print(f"[CLIENT THREAD STARTED] {addr}")

    ip = addr[0]


    if ip not in connected_ips:
         connected_ips.append(ip)

    print(f"[CONNECTED] {addr}")
    print(f"[CLIENT PORT LIST] {[addr[1]]}")

    while True:
        try:
            data = conn.recv(1024).decode() 

            if not data:
                break
            cmd_parts = data.strip().split()

            if len(cmd_parts) == 0:
                response = "[ERROR] Empty command"

            else:
                command = cmd_parts[0]

                            
###################################################################
# ingest call function
###################################################################
                if command == "INGEST":
                    
                    if not write_semaphore.acquire(blocking=False):
                        response = f"Server currently writing to memory, try again later. "
                        conn.send(response.encode())
                        try:
                            conn.sendall(response.encode())
                        finally:
                            conn.close()   
                        return 
                    try:
                       response = ingest(syslog_entries, conn, data)
                    finally:
                        write_semaphore.release()
###################################################################
# purge call function
###################################################################
                elif command == "PURGE":

                    if not write_semaphore.acquire(blocking=False):
                        response = f"Server currently being purged, try again later. "
                        try:
                            conn.sendall(response.encode())
                        finally:
                            conn.close()   
                        return 
                    else:
                        try:
                            response = purge(syslog_entries)
                        finally:
                            write_semaphore.release()

###################################################################
# query call function
###################################################################
                elif command == "QUERY":

                    if not query_semaphore.acquire(blocking=False):
                        response = "Server currently handling another query, try again later."
                        try:
                            conn.sendall(response.encode())
                        finally:
                            conn.close()   
                        return 
                    else:
                        try:
                            response = query(data,syslog_entries, )
                        finally:
                            query_semaphore.release()


###################################################################
# function return section
###################################################################
                else:
                    response = f"Unknown command: {command}, type 'HELP' for available commands."


            try:
                conn.send(response.encode())
            except AttributeError as e:
                    print(f"[SERVER PURGED] Server has been purged, QUERY request from {addr}: {e} cannot be done.")
                    response = "Server has no logs, QUERY cannot be done."
                    conn.send(response.encode())
                    break
            except OSError as e:
                if getattr(e, "winerror", None) in (10053, 10054):
                    print(f"[ABRUPT DISCONNECT] {addr}: {e}")
                    break
                raise


        except (ConnectionResetError, ConnectionAbortedError):
            print(f"[ABRUPT DISCONNECT during recv] {addr}")
            break


    conn.close()
    print(f"[DISCONNECTED] {addr}")
    if ip in connected_ips:
        connected_ips.remove(ip)


###################################################################
# thread/connection initialization function
###################################################################
def connection_handler(server):
    print("[ACCEPT THREAD STARTED]")

    while True:
        conn, addr = server.accept()

        global client_thread 
        client_thread = threading.Thread(target=handle_client,args=(conn, addr))
        client_thread.start() 
        

###################################################################
# server initialization function
###################################################################
def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(5)

    print(f"Server listening on {HOST}:{PORT}...")

    accept_thread = threading.Thread(
        target=connection_handler, 
        args=(server,)
    )
    accept_thread.start()


###################################################################
# server start call
###################################################################
#start_server()

###################################################################
# copypaste cli commands
###################################################################
#INGEST SVR1_server_auth_syslog.txt IP:11017
#INGEST SVR2_server_auth_syslog.txt IP:11017