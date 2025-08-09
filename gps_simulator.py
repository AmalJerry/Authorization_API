# import socket
# import time
# import os
# import django
# import requests
# from datetime import datetime

# # Django setup
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "API.settings")
# django.setup()

# from send_api.models import RFIDAuthorizationQueue, RFIDAuthorization

# HOST = '127.0.0.1'
# PORT = 9091


# def get_current_device_location():
#     try:
#         response = requests.get("http://ip-api.com/json/")
#         if response.status_code == 200:
#             data = response.json()
#             return float(data['lat']), float(data['lon'])
#         else:
#             print("❌ Failed to fetch device location. Status:", response.status_code)
#     except Exception as e:
#         print("❌ Error fetching location:", e)

#     return None, None


# def clean_rfid(rfid: str) -> str:
#     return rfid[:10] if len(rfid) > 10 else rfid


# def get_live_rfid_status(device_id, rfid) -> str:
#     try:
#         obj = RFIDAuthorization.objects.filter(device_id=device_id, rfid=rfid).latest('updated_at')
#         return "1" if obj.status == "Authorized" else "0"
#     except RFIDAuthorization.DoesNotExist:
#         return "0"


# def extract_rfids_from_command(command_string):
#     try:
#         core = command_string.strip().replace("$$:", "")
#         parts = core.split(",")
#         return [clean_rfid(r) for r in parts[3:]]
#     except Exception as e:
#         print(f"[RFID EXTRACT ERROR] {e}")
#         return []


# def parse_gps_data(reply: str):
#     try:
#         # Expected format: ":REPLY,...,lat=12.34,long=77.12,time=20250802163000"
#         gps_info = {}
#         for part in reply.split(","):
#             if "=" in part:
#                 key, value = part.split("=")
#                 gps_info[key.strip()] = value.strip()
#         latitude = gps_info.get("lat", None)
#         longitude = gps_info.get("long", None)
#         raw_time = gps_info.get("time", None)

#         # Format the time nicely if present
#         timestamp = (
#             datetime.strptime(raw_time, "%Y%m%d%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
#             if raw_time else None
#         )
#         return latitude, longitude, timestamp
#     except Exception as e:
#         print(f"[GPS PARSE ERROR] {e}")
#         return None, None, None


# def simulate_device():
#     queued_commands = RFIDAuthorizationQueue.objects.filter(is_sent=False).order_by('created_at')
    
#     if not queued_commands.exists():
#         print("🚫 No commands queued.")
#         return

#     for cmd in queued_commands:
#         try:
#             with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#                 s.connect((HOST, PORT))

#                 command_string = cmd.command_string.strip()
#                 parts = command_string.replace("$$:", "").split(",")

#                 if len(parts) < 4:
#                     print(f"[INVALID COMMAND] {command_string}")
#                     continue

#                 device_id = parts[1]
#                 command_code = parts[2]
#                 rfids = extract_rfids_from_command(command_string)

#                 # Step 1: Send original command
#                 s.sendall(command_string.encode())
#                 print(f"📤 RECV: {command_string}")

#                 # Step 2: Wait for REPLY from server (this is where GPS data comes in)

#                 # Step 3: Extract and print GPS data
#                 lat, lon = get_current_device_location()

#                 reply_data = s.recv(1024).decode().strip()

#                 if reply_data:
#                     print(f"📥 Server REPLY: {reply_data}")

#                     # Timestamp when REPLY was received
#                     timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
#                     # Get current location
#                     lat, lon = get_current_device_location()

#                     if lat is not None and lon is not None:
#                         print(f"📍 Device Location (from IP): Latitude = {lat}, Longitude = {lon}")
#                         reply_data += f",LAT={lat:.6f},LON={lon:.6f},TIMESTAMP={timestamp}"
#                     else:
#                         print("⚠️ Could not fetch GPS location of the device.")
#                         reply_data += f",TIMESTAMP={timestamp}"
                    
#                     print(f"📤 Modified REPLY Sent to Device: {reply_data}")
#                 else:
#                     print("⚠️ Server didn't send any REPLY.")


#                 # Step 4: Build REPLY for RFID authorization
#                 reply_statuses = []
#                 for rfid in rfids:
#                     status_code = get_live_rfid_status(device_id, rfid)
#                     reply_statuses.append(f"{rfid}={status_code}")
#                 reply_str = f":REPLY,{device_id},{command_code}," + ",".join(reply_statuses)

#                 # Step 5: Send REPLY for authorization
#                 s.sendall(reply_str.encode())
#                 print(f"📤 Sent REPLY: {reply_data}")

#                 # Mark as sent
#                 cmd.is_sent = True
#                 cmd.save()

#                 time.sleep(1)

#         except Exception as e:
#             print(f"[DEVICE ERROR] {e}")


# if __name__ == "__main__":
#     simulate_device()



import socket
import time
import os
import django

# Django setup
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "API.settings")
django.setup()

from send_api.models import RFIDAuthorizationQueue, RFIDAuthorization

HOST = '127.0.0.1'
PORT = 9091


def clean_rfid(rfid: str) -> str:
    """Removes checksum if length > 10."""
    return rfid[:10] if len(rfid) > 10 else rfid


def get_live_rfid_status(device_id, rfid) -> str:
    """Returns 1 if Authorized, 0 otherwise based on latest DB value."""
    try:
        obj = RFIDAuthorization.objects.filter(device_id=device_id, rfid=rfid).latest('updated_at')
        return "1" if obj.status == "Authorized" else "0"
    except RFIDAuthorization.DoesNotExist:
        return "0"  # default to Unauthorized if not found


def extract_rfids_from_command(command_string):
    """
    Example command_string: $$:31,862771075346091,146,0011667700,0009986090FE\r\n
    Extracts RFIDs, removes checksum from last one.
    """
    try:
        core = command_string.strip().replace("$$:", "")
        parts = core.split(",")
        return [clean_rfid(r) for r in parts[3:]]
    except Exception as e:
        print(f"[RFID EXTRACT ERROR] {e}")
        return []


def simulate_device():
    queued_commands = RFIDAuthorizationQueue.objects.filter(is_sent=False).order_by('created_at')
    
    if not queued_commands.exists():
        print("🚫 No commands queued.")
        return

    for cmd in queued_commands:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((HOST, PORT))

                command_string = cmd.command_string.strip()
                parts = command_string.replace("$$:", "").split(",")

                if len(parts) < 4:
                    print(f"[INVALID COMMAND] {command_string}")
                    continue

                device_id = parts[1]
                command_code = parts[2]

                rfids = extract_rfids_from_command(command_string)

                # 🔄 Check live DB status for each RFID
                reply_statuses = []
                for rfid in rfids:
                    status_code = get_live_rfid_status(device_id, rfid)
                    reply_statuses.append(f"{rfid}={status_code}")

                reply_str = f":REPLY,{device_id},{command_code}," + ",".join(reply_statuses)

                # 📤 Trigger server with original command
                s.sendall(command_string.encode())
                print(f"📤 RECV: {command_string}")

                # 🕒 Wait for response (echo)
                server_response = s.recv(1024).decode().strip()
                print(f"📥 Server sent: {server_response}")

                # 📤 Send actual REPLY
                s.sendall(reply_str.encode())
                print(f"📤REPLY: {reply_str}")

                # ✅ Mark as sent
                cmd.is_sent = True
                cmd.save()

                time.sleep(1)

        except Exception as e:
            print(f"[DEVICE ERROR] {e}")


if __name__ == "__main__":
    simulate_device()
