import socket

def start_persistent_server(host='0.0.0.0', port=9091):
    """Start a TCP server that listens indefinitely for data from an IoT device."""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(1)  # You can increase this for multiple devices

    print(f"[Server] Listening on {host}:{port}...")

    while True:
        conn, addr = server_socket.accept()
        print(f"[Server] Connected by {addr}")

        try:
            while True:
                data = conn.recv(1024)
                if not data:
                    print("[Server] Device disconnected.")
                    break

                message = data.decode('utf-8', errors='ignore')
                print(f"[Server] Received from {addr}: {message}")

                # Optionally send a response
                # conn.sendall(b"ACK")  
        except socket.error as e:
            print(f"[Server] Socket error: {e}")
        finally:
            conn.close()
            print(f"[Server] Connection with {addr} closed.")

if __name__ == "__main__":
    start_persistent_server()
