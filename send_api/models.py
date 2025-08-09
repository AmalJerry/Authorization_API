from django.db import models
from django.utils import timezone

# Create your models here.

class RFIDCommandLog(models.Model):
    ACTION_CHOICES = (
        ("Authorize", "Authorize"),
        ("Unauthorize", "Unauthorize"),
        ("CheckStatus", "CheckStatus"),
    )
    user_id = models.CharField(max_length=50)
    vehicle_id = models.CharField(max_length=50, null=True, blank=True) 
    device_id = models.CharField(max_length=20)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    rfid_list = models.JSONField()
    command_code = models.CharField(max_length=5)
    formatted_string = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.device_id} - {self.command_code} - {self.created_at}"



class RFIDAuthorization(models.Model):
    rfid = models.CharField(max_length=50, unique=True, db_index=True)
    status = models.CharField(max_length=20, null=True, blank=True, choices=[("Authorized", "Authorized"), ("Unauthorized", "Unauthorized")])
    device_id = models.CharField(max_length=50, null=True, blank=True)
    updated_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.rfid} - {self.status}"



class RFIDAuthorizationQueue(models.Model):
    device_id = models.CharField(max_length=50)
    vehicle_id = models.CharField(max_length=50, null=True, blank=True)
    command_string = models.TextField()
    command_code = models.CharField(max_length=10, null=True, blank=True, help_text="Command code sent to GPS device")
    is_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Queued Command for {self.device_id} - {self.command_string[:20]}..."


# class RFIDAuthorizationReply(models.Model):
#     device_id = models.CharField(max_length=50)
#     vehicle_id = models.CharField(max_length=50, null=True, blank=True)  # optional
#     command_code = models.CharField(max_length=5)
#     rfid = models.CharField(max_length=20)
#     status = models.CharField(max_length=10)  
#     received_at = models.DateTimeField(default=timezone.now)

#     def __str__(self):
#         return f"{self.device_id} | {self.rfid} = {self.status}"


# class RFIDAuthorizationCheck(models.Model):
#     """
#     Stores RFID status verification replies sent by the GPS device
#     in response to command code 146.
#     """
#     device_id = models.CharField(max_length=64, help_text="IMEI of the GPS device")
#     vehicle_id = models.CharField(max_length=64, null=True, blank=True, help_text="Optional vehicle identifier")
#     command_code = models.CharField(max_length=10, default="146", help_text="Command code sent to GPS device")
#     rfid = models.CharField(max_length=500, help_text="RFID number sent for verification")
#     status = models.CharField(
#         max_length=16,
#         choices=[
#             ("Authorized", "Authorized"),
#             ("Unauthorized", "Unauthorized"),
#             ("Unknown", "Unknown")
#         ],
#         help_text="Status reported by GPS device"
#     )
#     received_at = models.DateTimeField(default=timezone.now, help_text="Time when REPLY received")
#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"{self.device_id} - {self.rfid} = {self.status}"


class RFIDAuthorizationReply(models.Model):
    device_id = models.CharField(max_length=50)
    vehicle_id = models.CharField(max_length=50, null=True, blank=True)
    command_code = models.CharField(max_length=5)
    rfid = models.CharField(max_length=20)
    status = models.CharField(max_length=10)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    gps_timestamp = models.CharField(max_length=32, null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    received_at = models.DateTimeField(default=timezone.now, null=True, blank=True)

    def __str__(self):
        return f"{self.device_id} | {self.rfid} = {self.status}"



class RFIDAuthorizationCheck(models.Model):
    device_id = models.CharField(max_length=64)
    vehicle_id = models.CharField(max_length=64, null=True, blank=True)
    command_code = models.CharField(max_length=10, default="146")
    rfid = models.CharField(max_length=500)
    status = models.CharField(
        max_length=16,
        choices=[
            ("Authorized", "Authorized"),
            ("Unauthorized", "Unauthorized"),
            ("Unknown", "Unknown")
        ]
    )
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    gps_timestamp = models.CharField(max_length=32, null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    received_at = models.DateTimeField(default=timezone.now, null=True, blank=True)

    def __str__(self):
        return f"{self.device_id} - {self.rfid} = {self.status}"