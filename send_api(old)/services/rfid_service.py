# utils.py or services/rfid_service.py
from send_api.models import RFIDAuthorization

def process_rfid_action(rfids, device_id, action):
    result = {}

    for rfid in rfids:
        if action == "CheckStatus":
            try:
                current = RFIDAuthorization.objects.get(rfid=rfid)
                result[rfid] = current.status
            except RFIDAuthorization.DoesNotExist:
                result[rfid] = "Unknown"
        else:
            status = "Authorized" if action == "Authorize" else "Unauthorized"
            RFIDAuthorization.objects.update_or_create(
                rfid=rfid,
                defaults={"status": status, "device_id": device_id}
            )
            result[rfid] = status

    return result
