import socket
import datetime
import os
import django
import geocoder
from django.utils.timezone import now
from send_api.helpers import parse_gps_reply_data
from send_api.env_command_utils import get_unsent_commands_for_device, mark_command_as_sent


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "API.settings")
django.setup()

from send_api.models import RFIDAuthorizationQueue, RFIDAuthorizationReply, RFIDAuthorizationCheck

HOST = '0.0.0.0'
PORT = 9091
LOG_FILE = 'iot_data.log'

def get_device_location(ip_address):
    g = geocoder.ip(ip_address)
    if g.ok and g.latlng:
        return {
            "latitude": g.latlng[0],
            "longitude": g.latlng[1],
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    return {
        "latitude": None,
        "longitude": None,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


def log_data(client_ip, direction, data):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] {direction} {client_ip}: {data}"
    print(log_entry)
    with open(LOG_FILE, 'a') as f:
        f.write(log_entry + "\n")

def clean_rfid(rfid: str) -> str:
    return rfid[:-2] if len(rfid) > 10 else rfid

def save_reply_entry(device_id, vehicle_id, command_code, status, latitude=None, longitude=None, gps_timestamp=None):
    RFIDAuthorizationReply.objects.create(
        device_id=device_id,
        vehicle_id=vehicle_id,
        command_code=command_code,
        rfid=None,
        status=status,
        latitude=None,
        longitude=None,
        gps_timestamp=None,
        received_at=now()
    )
    print(f"[REPLY SAVED] Device: {device_id}, Code: {command_code}, Status: {status}")

def save_check_status_entry_from_reply(reply_raw, latitude=None, longitude=None, gps_timestamp=None):
    try:
        if reply_raw.startswith("$$:REPLY,"):
            payload = reply_raw.replace("$$:REPLY,", "").strip()
        elif reply_raw.startswith("&&:REPLY,"):
            payload = reply_raw.replace("&&:REPLY,", "").strip()
        elif reply_raw.startswith(":REPLY,"):
            payload = reply_raw.replace(":REPLY,", "").strip()
        elif reply_raw.startswith(","):
            payload = reply_raw.replace(",", "").strip()
        else:
            print(f"[REPLY IGNORED] Unrecognized prefix in CheckStatus: {reply_raw}")
            return

        parts = payload.split(",", 2)
        if len(parts) < 3:
            print(f"[CHECK REPLY ERROR] Malformed REPLY: {reply_raw}")
            return

        device_id = parts[0]
        command_code = parts[1]
        if command_code != "146":
            print(f"[CHECK REPLY IGNORED] Not a CheckStatus REPLY")
            return

        rfid_pairs = parts[2].split(",")

        for pair in rfid_pairs:
            if "=" not in pair:
                continue

            rfid_raw, status_val = pair.split("=")
            rfid_cleaned = clean_rfid(rfid_raw.strip())
            status_text = "Authorized" if status_val.strip() == "1" else "Unauthorized"

            # Save to Check table
            RFIDAuthorizationCheck.objects.create(
                device_id=device_id,
                rfid=rfid_cleaned,
                status=status_text,
                received_at=now(),
                latitude=latitude,
                longitude=longitude,
                gps_timestamp=gps_timestamp
            )
            print(f"[STATUS CHECK SAVED] {rfid_cleaned} = {status_text}")

    except Exception as e:
        print(f"[CHECK STATUS PARSE ERROR] {e}")

def extract_device_id(decoded):
    for part in decoded.split(","):
        if part.isdigit() and len(part) >= 10:
            return part
    return "UNKNOWN"


def parse_reply_and_store(reply_str, vehicle_id=None, latitude=None, longitude=None, gps_timestamp=None):
    try:
        if reply_str.startswith("$$:REPLY,"):
            payload = reply_str.replace("$$:REPLY,", "").strip()
        elif reply_str.startswith("&&:REPLY,"):
            payload = reply_str.replace("&&:REPLY,", "").strip()
        elif reply_str.startswith(":REPLY,"):
            payload = reply_str.replace(":REPLY,", "").strip()
        elif reply_str.startswith(","):
            payload = reply_str.replace(",", "").strip()
        else:
            print(f"[REPLY IGNORED] Unrecognized prefix: {reply_str}")
            return

        parts = payload.split(",", 2)
        if len(parts) < 3:
            print(f"[REPLY ERROR] Malformed REPLY: {reply_str}")
            return

        device_id = parts[0]
        command_code = parts[1]

        if command_code == "146":
            rfid_pairs = parts[2].split(",")

            for pair in rfid_pairs:
                if "=" not in pair:
                    continue

                rfid_raw, status_val = pair.split("=")
                rfid_cleaned = clean_rfid(rfid_raw.strip())

                if not rfid_cleaned:
                    continue

                status = (
                    "Authorized" if status_val.strip() == "1"
                    else "Unauthorized" if status_val.strip() == "0"
                    else "Unknown"
                )

                # ✅ Save to RFIDAuthorizationCheck table
                RFIDAuthorizationCheck.objects.create(
                    device_id=device_id,
                    rfid=rfid_cleaned,
                    status=status,
                    received_at=now()
                )

                print(f"[STATUS CHECK SAVED] {rfid_cleaned} = {status}")

            return 

        rfid_pairs = parts[2].split(",")

        for pair in rfid_pairs:
            if "=" not in pair:
                continue

            rfid_raw, status_val = pair.split("=")
            rfid_cleaned = clean_rfid(rfid_raw.strip())

            if not rfid_cleaned:
                continue

            status = (
                "Authorized" if status_val.strip() == "1"
                else "Unauthorized" if status_val.strip() == "0"
                else "Unknown"
            )

            # 🔄 Check for existing entry
            existing = RFIDAuthorizationReply.objects.filter(
                device_id=device_id,
                rfid=rfid_cleaned
            ).first()

            if existing:
                existing.status = status
                existing.command_code = command_code
                existing.received_at = now()
                existing.latitude = latitude
                existing.longitude = longitude
                existing.gps_timestamp = gps_timestamp
                existing.save()
                print(f"[REPLY UPDATED] {device_id} - {rfid_cleaned} = {status}")
            else:
                RFIDAuthorizationReply.objects.create(
                    device_id=device_id,
                    vehicle_id=vehicle_id,
                    command_code=command_code,
                    rfid=rfid_cleaned,
                    status=status,
                    received_at=now(),
                    latitude=latitude,
                    longitude=longitude,
                    gps_timestamp=gps_timestamp
                )
                print(f"[REPLY SAVED] {device_id} - {rfid_cleaned} = {status}")

    except Exception as e:
        print(f"[REPLY PARSE ERROR] {e}")

def start_server():
    HOST = "0.0.0.0"
    PORT = 9091

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        print(f"[LISTENING] Server running on {HOST}:{PORT}...")

        while True:
            conn, addr = s.accept()
            with conn:
                client_ip = addr[0]
                print(f"[CONNECTED] {client_ip}")

                try:
                    data = conn.recv(1024)
                    if not data:
                        continue

                    decoded = data.decode('utf-8', errors='replace').strip()
                    log_data(client_ip, "[RECEIVE]", decoded)

                    device_id = extract_device_id(decoded)
                    pending_cmds = get_unsent_commands_for_device(device_id)

                    if not pending_cmds:
                        log_data(client_ip, "[SEND]", f"[SKIP] No command for {device_id}")
                        continue

                    for cmd in pending_cmds:
                        command_string = cmd["command_string"]
                        conn.sendall(command_string.encode('utf-8'))
                        log_data(client_ip, "[SEND]", command_string)

                        conn.settimeout(50)
                        try:
                            reply = conn.recv(1024)
                            if reply:
                                reply_str = reply.decode('utf-8', errors='replace').strip()

                                # 🌐 Fetch dynamic lat/lon/timestamp using IP
                                gps = get_device_location(client_ip)
                                # Extract command_code from reply_str
                                command_code = None
                                if reply_str.startswith("$$:REPLY,"):
                                    payload = reply_str.replace("$$:REPLY,", "").strip()
                                elif reply_str.startswith("&&:REPLY,"):
                                    payload = reply_str.replace("&&:REPLY,", "").strip()
                                elif reply_str.startswith(":REPLY,"):
                                    payload = reply_str.replace(":REPLY,", "").strip()
                                elif reply_str.startswith(","):
                                    payload = reply_str.replace(",", "").strip()
                                else:
                                    payload = reply_str.strip()
                                parts = payload.split(",", 2)
                                if len(parts) >= 2:
                                    command_code = parts[1]
                                latitude = gps["latitude"]
                                longitude = gps["longitude"]
                                gps_timestamp = gps["timestamp"]
                                vehicle_id = None  # Set vehicle_id to None or extract if available
                                if command_code == "146":
                                    # This is a CHECK STATUS reply
                                    save_check_status_entry_from_reply(
                                        reply_str,
                                        latitude=latitude,
                                        longitude=longitude,
                                        gps_timestamp=gps_timestamp
                                    )
                                else:
                                    # This is a normal REPLY
                                    parse_reply_and_store(
                                        reply_str,
                                        vehicle_id=vehicle_id,
                                        latitude=latitude,
                                        longitude=longitude,
                                        gps_timestamp=gps_timestamp
                                    )
                                log_data(client_ip, "[REPLY]", reply_str)
                                print(f"📍 Device Location: Latitude = {gps['latitude']}, Longitude = {gps['longitude']}, 🕒 Timestamp: {gps['timestamp']}")
                              
                                # Optionally combine everything into one log
                                combined_reply = {
                                    "[SEND]": command_string,
                                    "[REPLY]": reply_str,
                                    "[LATITUDE]": gps["latitude"],
                                    "[LONGITUDE]": gps["longitude"],
                                    "[TIMESTAMP]": gps["timestamp"]
                                }
                                log_data(client_ip, "[COMBINED REPLY]", combined_reply)

                                # ⛳ Mark command as sent
                                mark_command_as_sent(command_string)
                                RFIDAuthorizationQueue.objects.filter(command_string=command_string).update(is_sent=True)
                            else:
                                log_data(client_ip, "[REPLY]", "Empty REPLY received")
                        except socket.timeout:
                            log_data(client_ip, "[REPLY]", "No REPLY received (timeout)")

                            RFIDAuthorizationQueue.objects.filter(
                                device_id=cmd["device_id"],
                                command_string=command_string,
                                is_sent=False
                            ).update(is_sent=True)

                except Exception as e:
                    print(f"[SOCKET ERROR]: {e}")

if __name__ == "__main__":
    try:
        start_server()
    except KeyboardInterrupt:
        print("[SHUTDOWN] Server manually stopped.")


