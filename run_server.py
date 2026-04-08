from Server.Server import start_server
import sys

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python run_server.py <HOST> <PORT>")
        sys.exit(1)

    HOST = sys.argv[1]
    PORT = int(sys.argv[2])

    start_server(HOST, PORT)