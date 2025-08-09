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