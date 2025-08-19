from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .serializers import RFIDAuthorizationQueueSerializer, RFIDCommandSerializer, RFIDAuthorizationReplySerializer
from .models import RFIDCommandLog, RFIDAuthorizationReply, RFIDAuthorizationQueue, RFIDAuthorizationCheck
from rest_framework import viewsets
from rest_framework.generics import CreateAPIView
import subprocess
from rest_framework.decorators import api_view

import time
import redis

redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)

class RFIDCommandAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = RFIDCommandSerializer(data=request.data, context={"request": request})
        
        if not serializer.is_valid():
            return self.error_response(
                message="Validation failed",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        instance = serializer.save()
        action = request.data.get("Action")

        # Handle CheckStatus
        if action in ["CheckStatus", "146"]:
            rfids = request.data.get("RFIDs")
            if not rfids or not isinstance(rfids, list):
                return self.error_response(
                    message="Invalid RFIDs input",
                    errors={"RFIDs": "Must be a non-empty list"},
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            rfid_value = rfids[0]
            reply = RFIDAuthorizationCheck.objects.filter(rfid=rfid_value).order_by('-received_at').first()

            if reply:
                return self.success_response(
                    message="RFID status retrieved",
                    data={
                        "rfid": rfid_value,
                        "status": "Authorized" if reply.status == "Authorized" else "Unauthorized",
                        "timestamp": reply.received_at
                    }
                )
            else:
                return self.error_response(
                    message="No authorization reply found for this RFID",
                    errors={"rfid": rfid_value},
                    status_code=status.HTTP_404_NOT_FOUND
                )

        # Default response for command generation
        return self.success_response(
            message="Command generated successfully",
            data={
                "command": instance.formatted_string,
                "user_id": instance.user_id
            },
            status_code=status.HTTP_201_CREATED
        )

    # Success response helper
    def success_response(self, message, data=None, status_code=status.HTTP_200_OK):
        return Response({
            "success": True,
            "message": message,
            "data": data,
            "errors": None
        }, status=status_code)

    # Error response helper
    def error_response(self, message, errors=None, status_code=status.HTTP_400_BAD_REQUEST):
        return Response({
            "success": False,
            "message": message,
            "data": None,
            "errors": errors
        }, status=status_code)


class RFIDAuthorizationQueueCreateView(CreateAPIView):
    queryset = RFIDAuthorizationQueue.objects.all()
    serializer_class = RFIDAuthorizationQueueSerializer
    permission_classes = [permissions.IsAuthenticated]


class RFIDAuthorizationReplyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = RFIDAuthorizationReply.objects.all().order_by('-received_at')
    serializer_class = RFIDAuthorizationReplySerializer



# import json
# import subprocess
# import socket
# from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt
# from django.views.decorators.http import require_POST


# LINUX_SERVICES = ["tcp.service", "tcp_send.service"]
# PORT = 9091


# def is_port_in_use(port):
#     with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#         return s.connect_ex(("166.0.242.173", port)) == 0


# def who_owns_port(port):
#     try:
#         result = subprocess.check_output(f"lsof -i :{port}", shell=True).decode()
#         for service in LINUX_SERVICES:
#             if service.split('.')[0] in result:
#                 return service
#     except subprocess.CalledProcessError:
#         pass
#     return None


# def control_linux_service(action, service_name):
#     try:
#         if action == "start":
#             cmd = f" systemctl start {service_name}"
#         elif action == "stop":
#             cmd = f" systemctl stop {service_name}"
#         elif action == "restart":
#             cmd = f" systemctl restart {service_name}"
#         elif action == "status":
#             cmd = f"systemctl status {service_name}"
#         else:
#             return False, f"Unknown action '{action}'"

#         result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
#         if result.returncode == 0:
#             return True, result.stdout
#         else:
#             return False, result.stderr
#     except Exception as e:
#         return False, str(e)


# @csrf_exempt
# @require_POST
# def service_control(request):
#     try:
#         data = json.loads(request.body)
#         action = data.get("action")
#         target = data.get("service")

#         if action not in ["start", "stop", "restart", "status"]:
#             return JsonResponse({"error": "Invalid action"}, status=400)

#         if target not in LINUX_SERVICES:
#             return JsonResponse({"error": "Invalid service"}, status=400)

#         # Only check port when starting
#         if action == "start":
#             if is_port_in_use(PORT):
#                 active_service = who_owns_port(PORT)
#                 if active_service and active_service != target:
#                     return JsonResponse({
#                         "error": f"Port {PORT} is already in use by '{active_service}'. Please stop it before starting '{target}'."
#                     }, status=409)

#         success, output = control_linux_service(action, target)

#         if success:
#             return JsonResponse({
#                 "message": f"Service '{target}' {action}ed successfully.",
#                 "output": output
#             })
#         else:
#             return JsonResponse({
#                 "error": f"Failed to {action} service '{target}'",
#                 "output": output
#             }, status=500)

#     except Exception as e:
#         return JsonResponse({"error": str(e)}, status=500)


import json
import subprocess
import socket
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST


LINUX_SERVICES = ["tcp.service", "tcp_send.service"]
PORT = 9091
SERVER_IP = "166.0.242.173"


def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((SERVER_IP, port)) == 0


def who_owns_port(port):
    try:
        result = subprocess.check_output(f"lsof -i :{port}", shell=True).decode()
        for service in LINUX_SERVICES:
            if service.split('.')[0] in result:
                return service
    except subprocess.CalledProcessError:
        pass
    return None


def get_service_status(service_name):
    try:
        result = subprocess.check_output(f"systemctl is-active {service_name}", shell=True).decode().strip()
        return result  # active | inactive | failed | activating | deactivating
    except subprocess.CalledProcessError:
        return "Inactive"


def control_linux_service(action, service_name):
    try:
        cmd = f"systemctl {action} {service_name}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            return True, result.stdout
        else:
            return False, result.stderr
    except Exception as e:
        return False, str(e)


@csrf_exempt
@require_POST
def service_control(request):
    try:
        data = json.loads(request.body)
        action = data.get("action")
        target = data.get("service")

        if action not in ["start", "stop", "restart", "status"]:
            return JsonResponse({"error": "Invalid action"}, status=400)

        if target not in LINUX_SERVICES:
            return JsonResponse({"error": "Invalid service"}, status=400)

        current_status = get_service_status(target)

        if action == "start":
            if current_status == "Active":
                return JsonResponse({
                    "message": f"'{target}' is already started and currently Active."
                })

            # Check if the port is in use
            if is_port_in_use(PORT):
                owner_service = who_owns_port(PORT)
                if owner_service and owner_service != target:
                    return JsonResponse({
                        "warning": f"The port {PORT} is already in use by '{owner_service}'. Please stop it before starting '{target}'."
                    }, status=409)

            # Start the service only if port is free or owned by this service
            success, output = control_linux_service("start", target)

            if success:
                return JsonResponse({
                    "message": f"Service '{target}' started successfully."
                })
            else:
                return JsonResponse({
                    "error": f"Failed to start service '{target}'",
                    "output": output
                }, status=500)

        elif action == "stop":
            if current_status == "Inactive":
                return JsonResponse({
                    "message": f"'{target}' is already stopped and currently inactive."
                })

        elif action == "status":
            return JsonResponse({
                "service": target,
                "status": current_status
            })

        # Run the command (start, stop, restart)
        success, output = control_linux_service(action, target)

        if success:
            return JsonResponse({
                "message": f"Service '{target}' {action}ed successfully.",
                "output": output
            })
        else:
            return JsonResponse({
                "error": f"Failed to {action} service '{target}'",
                "output": output
            }, status=500)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)   

