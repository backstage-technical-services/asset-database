from django.contrib import admin
from .models import *


class ItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'itemclass', 'owner', 'is_channel', 'is_multichannel')
    list_filter = ('itemclass', 'owner', 'is_channel', 'is_multichannel')
    list_editable = ('itemclass', 'owner', 'is_channel', 'is_multichannel')


# Register your models here.
admin.site.register(Tester)
admin.site.register(Department)
admin.site.register(Category)
admin.site.register(Subcategory)
admin.site.register(Item, ItemAdmin)
admin.site.register(ItemClass)
admin.site.register(Owner)
