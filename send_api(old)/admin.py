from django.contrib import admin
from .models import RFIDCommandLog, RFIDAuthorizationReply, RFIDAuthorizationQueue, RFIDAuthorization, RFIDAuthorizationCheck
from django.utils import timezone
from django.utils.timezone import now
from django.utils import timezone
# Register your models here.


@admin.register(RFIDCommandLog)
class RFIDCommandLogAdmin(admin.ModelAdmin):
    list_display = ('device_id', 'command_code',  'created_at')
    search_fields = ('device_id', 'command_code')
    list_filter = ('created_at', 'action')


@admin.register(RFIDAuthorizationReply)
class RFIDAuthorizationReplyAdmin(admin.ModelAdmin):
    list_display = ('device_id', 'command_code', 'rfid', 'status', 'received_at')
    search_fields = ('device_id', 'command_code', 'rfid')
    list_filter = ('status', 'received_at')


@admin.register(RFIDAuthorizationQueue)
class RFIDAuthorizationQueueAdmin(admin.ModelAdmin):
    list_display = ('id', 'device_id', 'command_string', 'is_sent', 'created_at')
    search_fields = ('device_id', 'command_string')
    list_filter = ('is_sent', 'created_at')


@admin.register(RFIDAuthorization)
class RFIDAuthorizationAdmin(admin.ModelAdmin):
    list_display = ('rfid', 'status', 'device_id', 'updated_at')
    search_fields = ('rfid', 'device_id')
    list_filter = ('status', 'updated_at')

@admin.register(RFIDAuthorizationCheck)
class RFIDAuthorizationCheckAdmin(admin.ModelAdmin):
    list_display = ('device_id', 'rfid', 'status', 'received_at')
    search_fields = ('device_id', 'rfid')
    list_filter = ('status', 'received_at')

    def get_queryset(self, request):
        # Override to filter by today's date
        qs = super().get_queryset(request)
        return qs.filter(received_at__date=now().date())