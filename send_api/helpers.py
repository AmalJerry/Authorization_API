def map_action_to_code(action):
    mapping = {
        "Authorize": "144",
        "Unauthorize": "145",
        "CheckStatus": "146"
    }
    return mapping.get(action)


def format_rfid(rfid):
    return rfid.zfill(10)


def calculate_length(device_id, command_code, rfids):
    body = f",{device_id},{command_code}," + ",".join(rfids)
    return len(body)


def calculate_checksum(packet: str) -> str:
    """
    Calculate the 2-digit uppercase hexadecimal checksum for the full packet string,
    including '$$:<length>' and all content before the checksum.
    Example input:
        "$$:42,862688071537186,146,0011667761,0011611859"
    """
    ascii_sum = sum(ord(char) for char in packet)
    checksum = ascii_sum & 0xFF
    return f"{checksum:02X}"

def parse_gps_reply_data(reply_raw):
    """
    Extract latitude, longitude, and timestamp from the REPLY packet.
    Expected format:
    $$:<len>,<imei>,REPLY,<code>,<rfids>,<device_id>,<timestamp>,<lat>,<lon>,<status>
    """
    try:
        # Remove prefix $$: and split by comma
        if reply_raw.startswith("$$:REPLY,"):
            payload = reply_raw.replace("$$:REPLY,", "").strip()
        elif reply_raw.startswith("&&:REPLY,"):
            payload = reply_raw.replace("&&:REPLY,", "").strip()
        elif reply_raw.startswith(":REPLY,"):
            payload = reply_raw.replace(":REPLY,", "").strip()
        else:
            print(f"[REPLY IGNORED] Unrecognized prefix: {reply_raw}")
            return

        parts = payload.strip().split(',')

        # Make sure we have at least 10 elements
        if len(parts) >= 10 and parts[2] == "REPLY":
            timestamp = parts[7]
            latitude = parts[8]
            longitude = parts[9]
            return {
                "timestamp": timestamp,
                "latitude": latitude,
                "longitude": longitude
            }
        else:
            print("[REPLY PARSE ERROR]: Unexpected format or missing data.")
            return None
    except Exception as e:
        print(f"[REPLY PARSE EXCEPTION]: {e}")
        return None
