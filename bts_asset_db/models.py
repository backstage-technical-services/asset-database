from django.db import models
from django.core import validators
from django.core.exceptions import ObjectDoesNotExist


class Item(models.Model):
    asset_id = models.CharField(max_length=15)
    itemclass = models.ForeignKey('ItemClass', on_delete=models.PROTECT, related_name="member_item_set",
                                  blank=True, null=True)
    storage = models.ForeignKey('self', on_delete=models.SET_NULL, blank=True, null=True, related_name="stored_item_set")
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, blank=True, null=True, related_name="children_set")
    associations = models.ManyToManyField('ItemClass', related_name="associated_item_set", blank=True)
    owner = models.ForeignKey('Owner', on_delete=models.DO_NOTHING, blank=True, null=True)
    make = models.CharField(max_length=32, blank=True, null=True)
    model = models.CharField(max_length=32, blank=True, null=True)
    serial_number = models.CharField(max_length=32, blank=True, null=True)
    value = models.IntegerField(blank=True, null=True)
    is_identifiable = models.BooleanField(default=True)
    is_location = models.BooleanField(default=False)
    is_multichannel = models.BooleanField(default=False)
    is_channel = models.BooleanField(default=False)
    is_consumable = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    processed = models.BooleanField(default=False)

    def __str__(self):
        return str(self.asset_id)

    def redefine_all_records(self, new_item):
        for record in self.record_set.all():
            record.change_item(new_item)


class ItemClass(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    subcategory = models.ForeignKey('Subcategory', on_delete=models.PROTECT)

    def __str__(self):
        return f"{self.name}"  # f"{self.subcategory.name} > {self.name}"


class Subcategory(models.Model):
    name = models.CharField(max_length=32)
    category = models.ForeignKey('Category', on_delete=models.PROTECT)

    def __str__(self):
        return f"{self.name}"  # f"{self.category.department.name} > {self.category.name} > {self.name}"


class Category(models.Model):
    name = models.CharField(max_length=32)
    department = models.ForeignKey('Department', on_delete=models.PROTECT)

    def __str__(self):
        return f"{self.department.name} > {self.name}"


class Department(models.Model):
    name = models.CharField(max_length=32)

    def __str__(self):
        return str(self.name)


class Owner(models.Model):
    name = models.CharField(max_length=32)

    def __str__(self):
        return str(self.name)


class Tester(models.Model):
    first_name = models.CharField(max_length=32)
    last_name = models.CharField(max_length=32)
    initials = models.CharField(max_length=10, unique=True)
    pat_level = models.IntegerField(validators=[validators.MaxValueValidator(3), validators.MinValueValidator(1)])
    vis_level = models.IntegerField(validators=[validators.MaxValueValidator(3), validators.MinValueValidator(1)])
    machine_name = models.CharField(max_length=10, blank=True, null=True, unique=True)
    alt_machine_name = models.CharField(max_length=10, blank=True, null=True, unique=True)
    archived = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Record(models.Model):
    item = models.ForeignKey('Item', on_delete=models.PROTECT)
    timestamp = models.DateTimeField()
    site = models.CharField(max_length=15)
    location = models.CharField(max_length=15)
    tester = models.ForeignKey('Tester', on_delete=models.PROTECT)
    testcode_1 = models.CharField(max_length=10)
    testcode_2 = models.CharField(max_length=10)
    machine_serial_no = models.ForeignKey('TestingMachine', to_field="serial_number",
                                          db_column="machine_serial_no", on_delete=models.PROTECT)
    machine_firmware_version = models.CharField(max_length=6)
    retest_freq_months = models.IntegerField()
    user_data_input_order = models.CharField(max_length=12)
    item_make = models.CharField(max_length=83, blank=True, null=True)
    item_model = models.CharField(max_length=83, blank=True, null=True)
    item_description = models.CharField(max_length=83, blank=True, null=True)
    item_notes = models.CharField(max_length=83, blank=True, null=True)
    item_group = models.CharField(max_length=83, blank=True, null=True)
    item_serial_number = models.CharField(max_length=83, blank=True, null=True)

    def __str__(self):
        return f'Record {self.id}, Item {self.item.asset_id}'

    def change_item(self, item_id):
        try:
            new_item = Item.objects.get(asset_id=item_id)
        except ObjectDoesNotExist:
            print("Item does not exist!")
        else:
            self.item = new_item
            self.save()


class PatTest(models.Model):
    record = models.ForeignKey(Record, models.PROTECT)
    test_type = models.IntegerField()
    test_parameter_1 = models.CharField(max_length=5, blank=True, null=True)
    test_parameter_2 = models.CharField(max_length=18, blank=True, null=True)
    test_parameter_3 = models.CharField(max_length=6, blank=True, null=True)

    def __str__(self):
        return str(self.id)


class VisualTest(models.Model):
    tester = models.ForeignKey('Tester', on_delete=models.PROTECT, related_name="visual_test_set",
                               limit_choices_to={'archived': False})
    timestamp = models.DateTimeField()
    item = models.ForeignKey('Item', on_delete=models.PROTECT)
    supervisor = models.ForeignKey('Tester', on_delete=models.PROTECT, limit_choices_to={'vis_level': 3,
                                                                                         'archived': False},
                                   related_name="visual_supervision_set", blank=True, null=True)
    notes = models.CharField(max_length=100, null=True, blank=True)
    failed = models.BooleanField()

    def __str__(self):
        return str(self.id)


class Repair(models.Model):
    repairer = models.ForeignKey('Tester', on_delete=models.PROTECT, related_name="repair_set",
                                 limit_choices_to={'archived': False})
    timestamp = models.DateTimeField()
    item = models.ForeignKey('Item', on_delete=models.PROTECT)
    supervisor = models.ForeignKey('Tester', on_delete=models.PROTECT, blank=True, null=True,
                                   limit_choices_to={'vis_level': 3, 'archived': False},
                                   related_name="repair_supervision_set")
    notes = models.CharField(max_length=100, null=True, blank=True)
    failed = models.BooleanField()

    def __str__(self):
        return str(self.id)


class TestingMachine(models.Model):
    serial_number = models.CharField(max_length=10, unique=True)
    last_imported_record_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return str(self.serial_number) + ": " + str(self.last_imported_record_time)
