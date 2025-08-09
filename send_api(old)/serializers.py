from rest_framework import serializers, viewsets
from .models import RFIDCommandLog, RFIDAuthorizationReply, RFIDAuthorizationQueue
from send_api.services.rfid_service import process_rfid_action
from .helpers import map_action_to_code, format_rfid, calculate_length, calculate_checksum
from .env_command_utils import add_command_to_env



class RFIDCommandSerializer(serializers.ModelSerializer):
    # Write-only fields from frontend
    vehicleId = serializers.CharField(write_only=True)
    deviceId = serializers.CharField(write_only=True)
    RFIDs = serializers.ListField(child=serializers.CharField(), write_only=True)
    Action = serializers.ChoiceField(choices=["Authorize", "Unauthorize", "CheckStatus"], write_only=True)

    class Meta:
        model = RFIDCommandLog
        fields = [
            'vehicleId', 'deviceId', 'RFIDs', 'Action',  
            'user_id', 'vehicle_id', 'device_id', 'rfid_list', 'action',  
            'command_code', 'formatted_string', 'created_at'
        ]
        read_only_fields = [
            'user_id', 'vehicle_id', 'device_id', 'rfid_list', 'action',
            'command_code', 'formatted_string', 'created_at'
        ]

    def validate(self, data):
        # Convert and map all input fields
        command_code = map_action_to_code(data["Action"])
        if not command_code:
            raise serializers.ValidationError("Invalid action.")

        formatted_rfids = [format_rfid(str(rfid)) for rfid in data["RFIDs"]]
        rfid_str = ",".join(formatted_rfids)
        body_part = f",{data['deviceId']},{command_code},{rfid_str}"

        length = len(body_part)
        cumulative_str = f"$$:{length}{body_part}"  # This is what checksum is based on

        checksum = calculate_checksum(cumulative_str)
        formatted_string = f"{cumulative_str}{checksum}\r\n"

        # Store mapped fields for model save
        self.cleaned_data = {
            "vehicle_id": data["vehicleId"],
            "device_id": data["deviceId"],
            "rfid_list": formatted_rfids,
            "action": data["Action"],
            "command_code": command_code,
            "formatted_string": formatted_string
        }

        return data
    

    def create(self, validated_data):
        request_user = self.context["request"].user
        device_id = self.cleaned_data["device_id"]
        vehicle_id = self.cleaned_data["vehicle_id"]
        formatted_string = self.cleaned_data["formatted_string"]
        rfid_list = self.cleaned_data["rfid_list"]
        action = self.cleaned_data["action"]

        # Save command to queue
        RFIDAuthorizationQueue.objects.create(
            device_id=device_id,
            vehicle_id=vehicle_id,
            command_string=formatted_string,
            is_sent=False
        )
        add_command_to_env(formatted_string, device_id, vehicle_id)
        # ✅ Update RFIDAuthorization table here
        process_rfid_action(rfid_list, device_id, action)

        # Log command
        return RFIDCommandLog.objects.create(
            user_id=str(request_user.id),
            **self.cleaned_data
        )


class RFIDAuthorizationQueueSerializer(serializers.ModelSerializer):
    class Meta:
        model = RFIDAuthorizationQueue
        fields = '__all__'
        read_only_fields = ['is_sent', 'created_at']


class RFIDAuthorizationReplySerializer(serializers.ModelSerializer):
    class Meta:
        model = RFIDAuthorizationReply
        fields = '__all__'
