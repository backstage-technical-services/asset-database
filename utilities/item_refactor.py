from bts_asset_db.models import Item, Records, VisualTests
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q


def bulk_remove_space_slash():
    all_items = Item.objects.filter(pk__contains=" /").values("id")
    for item in all_items:
        try:
            matching_item = Item.objects.get(pk=item['id'].replace(" /", "/"))
        except ObjectDoesNotExist:
            continue
        else:
            original_item = Item.objects.get(pk=item['id'])
            original_item.records_set.all().update(item=matching_item)


def bulk_remove_space():
    all_items = Item.objects.filter(pk__regex=r"\d\d\d\d \d$").values("id")
    for item in all_items:
        try:
            matching_item = Item.objects.get(pk=item['id'].replace(" ", "/"))
        except ObjectDoesNotExist:
            continue
        else:
            original_item = Item.objects.get(pk=item['id'])
            original_item.records_set.all().update(item=matching_item)


def bulk_rename_space():
    all_items = Item.objects.filter(pk__regex=r"\d\d\d\d \d$")
    for item in all_items:
        old_id = item.id
        new_id = old_id.replace(" ", "/")

        item.id = new_id
        item.save()

        old_item = Item.objects.get(pk=old_id)
        old_item.redefine_all_records(new_id)
        old_item.delete()


def bulk_rename_space_slash():
    all_items = Item.objects.filter(pk__contains=" /")
    for item in all_items:
        old_id = item.id
        new_id = old_id.replace(" /", "/").replace("/ ", "/")

        item.id = new_id
        item.save()

        old_item = Item.objects.get(pk=old_id)
        old_item.redefine_all_records(new_id)
        old_item.delete()

def find_orphaned_items():
    item_ids_records = Records.objects.values('item_id')
    item_ids_visuals = VisualTests.objects.values('item_id')
    orphans = Item.objects.exclude(Q(id__in=item_ids_records) |
                                   Q(id__in=item_ids_visuals))

    return orphans
