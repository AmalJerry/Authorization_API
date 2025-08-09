from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .serializers import RFIDAuthorizationQueueSerializer, RFIDCommandSerializer, RFIDAuthorizationReplySerializer
from .models import RFIDCommandLog, RFIDAuthorizationReply, RFIDAuthorizationQueue
from rest_framework import viewsets
from rest_framework.generics import CreateAPIView

import time
import redis

redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)

class RFIDCommandAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = RFIDCommandSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            instance = serializer.save()

            return Response({
                "message": "Command generated successfully.",
                "command": instance.formatted_string,
                "user_id": instance.user_id,
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RFIDAuthorizationQueueCreateView(CreateAPIView):
    queryset = RFIDAuthorizationQueue.objects.all()
    serializer_class = RFIDAuthorizationQueueSerializer
    permission_classes = [permissions.IsAuthenticated]


class RFIDAuthorizationReplyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = RFIDAuthorizationReply.objects.all().order_by('-received_at')
    serializer_class = RFIDAuthorizationReplySerializer