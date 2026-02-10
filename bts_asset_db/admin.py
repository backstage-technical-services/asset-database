from django.contrib import admin
from .models import *


class ItemAdmin(admin.ModelAdmin):
    list_display = ('asset_id', 'itemclass', 'owner', 'is_channel', 'is_multichannel')
    list_filter = ('owner', 'is_channel', 'is_multichannel')
    list_editable = ('itemclass', 'owner', 'is_channel', 'is_multichannel')

class TestingMachineAdmin(admin.ModelAdmin):
    list_display = ('id', 'serial_number', 'last_imported_record_time')
    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['title'] = "Testing Machines (Read-only)"
        return super().changelist_view(request, extra_context=extra_context)


# Register your models here.
admin.site.register(Tester)
admin.site.register(Department)
admin.site.register(Category)
admin.site.register(Subcategory)
admin.site.register(Item, ItemAdmin)
admin.site.register(ItemClass)
admin.site.register(Owner)
admin.site.register(TestingMachine, TestingMachineAdmin)