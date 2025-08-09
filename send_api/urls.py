from django.urls import path
from .views import RFIDCommandAPIView, RFIDAuthorizationQueueCreateView, RFIDAuthorizationReplyViewSet, service_control
from rest_framework.authtoken.views import obtain_auth_token

from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'reply-log', RFIDAuthorizationReplyViewSet, basename='reply-log')

urlpatterns = [
    path("api-token-auth/", obtain_auth_token),
    path("send-command/", RFIDCommandAPIView.as_view(), name="send-rfid-command"),
    path("queue-command/", RFIDAuthorizationQueueCreateView.as_view(), name='queue-command'),

    # Custom endpoint to control the service
    path('service-control/', service_control, name='control_service'),

]                                                                             
urlpatterns += router.urls
