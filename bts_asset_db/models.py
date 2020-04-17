from django.db import models
from django.core import validators
from django.core.exceptions import ObjectDoesNotExist


class ItemDescription(models.Model):
    record = models.OneToOneField('Records', models.DO_NOTHING, db_column='Record ID', primary_key=True)
    asset_description = models.CharField(db_column='Asset Description', max_length=20, blank=True, null=True)

    class Meta:
        db_table = 'item_description'

    def __str__(self):
        return self.asset_description


class ItemGroup(models.Model):
    record = models.OneToOneField('Records', models.DO_NOTHING, db_column='Record ID', primary_key=True)
    asset_group = models.CharField(db_column='Asset Group', max_length=20, blank=True, null=True)

    class Meta:
        db_table = 'item_group'

    def __str__(self):
        return self.asset_group


class ItemMake(models.Model):
    record = models.OneToOneField('Records', models.DO_NOTHING, db_column='Record ID', primary_key=True)
    make = models.CharField(db_column='Make', max_length=20, blank=True, null=True)

    class Meta:
        db_table = 'item_make'

    def __str__(self):
        return self.make


class ItemModel(models.Model):
    record = models.OneToOneField('Records', models.DO_NOTHING, db_column='Record ID', primary_key=True)
    model = models.CharField(db_column='Model', max_length=20, blank=True, null=True)

    class Meta:
        db_table = 'item_model'

    def __str__(self):
        return self.model


class ItemNotes(models.Model):
    record = models.OneToOneField('Records', models.DO_NOTHING, db_column='Record ID', primary_key=True)
    notes = models.CharField(db_column='Notes', max_length=20, blank=True, null=True)

    class Meta:
        db_table = 'item_notes'

    def __str__(self):
        return self.notes


class ItemSerialNumber(models.Model):
    record = models.OneToOneField('Records', models.DO_NOTHING, db_column='Record ID', primary_key=True)
    serial_number = models.CharField(db_column='Serial Number', max_length=20, blank=True, null=True)

    class Meta:
        db_table = 'item_serial_number'

    def __str__(self):
        return self.serial_number


class Records(models.Model):
    id = models.AutoField(db_column='Record ID', primary_key=True)
    item = models.ForeignKey('Item', on_delete=models.DO_NOTHING, db_column='Item ID')
    timestamp = models.DateTimeField(db_column='Timestamp')
    site = models.CharField(db_column='Site', max_length=15)
    location = models.CharField(db_column='Location', max_length=15)
    tester = models.ForeignKey('Tester', on_delete=models.DO_NOTHING, to_field="initials", db_column='Tester')
    testcode_1 = models.CharField(db_column='Testcode 1', max_length=10)
    testcode_2 = models.CharField(db_column='Testcode 2', max_length=10)
    serial_no = models.CharField(db_column='Serial No.', max_length=8)
    firmware_version = models.CharField(db_column='Firmware Version', max_length=6)
    retest_freq_months = models.IntegerField(db_column='Retest Freq. (Months)')
    user_data_input_order = models.CharField(db_column='User Data Input Order', max_length=12)

    class Meta:
        db_table = 'records'

    def __str__(self):
        return f'Record {self.id}, Item {self.item_id}'

    def change_item(self, item_id):
        try:
            new_item = Item.objects.get(pk=item_id)
        except ObjectDoesNotExist:
            print("Item does not exist!")
        else:
            self.item = new_item
            self.save()


class Tests(models.Model):
    id = models.AutoField(db_column='Test ID', primary_key=True)
    record = models.ForeignKey(Records, models.DO_NOTHING, db_column='Record ID')
    test_type = models.IntegerField(db_column='Test Type')
    test_parameter_1 = models.CharField(db_column='Test Parameter 1', max_length=5, blank=True, null=True)
    test_parameter_2 = models.CharField(db_column='Test Parameter 2', max_length=18, blank=True, null=True)
    test_parameter_3 = models.CharField(db_column='Test Parameter 3', max_length=6, blank=True, null=True)

    class Meta:
        db_table = 'tests'

    def __str__(self):
        return str(self.id)


class VisualTests(models.Model):
    id = models.AutoField(primary_key=True)
    tester = models.ForeignKey('Tester', on_delete=models.DO_NOTHING, related_name="visual_test_set")
    timestamp = models.DateTimeField()
    item = models.ForeignKey('Item', on_delete=models.DO_NOTHING)
    supervisor = models.ForeignKey('Tester', on_delete=models.DO_NOTHING, limit_choices_to={'vis_level': 3},
                                   related_name="visual_supervision_set", blank=True, null=True)
    notes = models.CharField(max_length=100, null=True, blank=True)
    failed = models.BooleanField()

    def __str__(self):
        return str(self.id)


class Repairs(models.Model):
    id = models.AutoField(primary_key=True)
    repairer = models.ForeignKey('Tester', on_delete=models.DO_NOTHING, related_name="repair_set")
    timestamp = models.DateTimeField()
    item = models.ForeignKey('Item', on_delete=models.DO_NOTHING)
    supervisor = models.ForeignKey('Tester', on_delete=models.DO_NOTHING, related_name="repair_supervision_set")
    notes = models.CharField(max_length=100, null=True, blank=True)
    failed = models.BooleanField()

    def __str__(self):
        return str(self.id)


class Tester(models.Model):
    id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=32)
    last_name = models.CharField(max_length=32)
    initials = models.CharField(max_length=10, unique=True)
    pat_level = models.IntegerField(validators=[validators.MaxValueValidator(3), validators.MinValueValidator(1)])
    vis_level = models.IntegerField(validators=[validators.MaxValueValidator(3), validators.MinValueValidator(1)])
    machine_name = models.CharField(max_length=10, blank=True, null=True, unique=True)
    alt_machine_name = models.CharField(max_length=10, blank=True, null=True, unique=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Department(models.Model):
    department = models.CharField(max_length=32)

    def __str__(self):
        return str(self.department)


class Category(models.Model):
    category = models.CharField(max_length=32)
    department = models.ForeignKey('Department', on_delete=models.DO_NOTHING)

    def __str__(self):
        return f"{self.department.department} > {self.category}"


class Subcategory(models.Model):
    subcategory = models.CharField(max_length=32)
    category = models.ForeignKey('Category', on_delete=models.DO_NOTHING)

    def __str__(self):
        return f"{self.category.department.department} > {self.category.category} > {self.subcategory}"


class ItemClass(models.Model):
    name = models.CharField(max_length=100)
    make = models.TextField(max_length=32, blank=True, null=True)
    model = models.TextField(max_length=32, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    subcategory = models.ForeignKey('Subcategory', on_delete=models.DO_NOTHING)

    def __str__(self):
        return f"{self.subcategory.subcategory} > {self.name}"


class Owner(models.Model):
    name = models.CharField(max_length=32)

    def __str__(self):
        return str(self.name)


class Item(models.Model):
    id = models.CharField(max_length=15, primary_key=True)
    itemclass = models.ForeignKey('ItemClass', on_delete=models.DO_NOTHING, related_name="member_item_set",
                                  blank=True, null=True)
    owner = models.ForeignKey('Owner', on_delete=models.DO_NOTHING, blank=True, null=True)
    serial_number = models.CharField(max_length=32, blank=True, null=True)
    storage = models.ForeignKey('self', on_delete=models.SET_NULL, blank=True, null=True,
                                related_name="stored_item_set")
    associations = models.ManyToManyField('ItemClass', related_name="associated_item_set", blank=True)
    is_identifiable = models.BooleanField()
    is_location = models.BooleanField()
    is_multichannel = models.BooleanField()
    is_channel = models.BooleanField()
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, blank=True, null=True, related_name="children_set")
    is_consumable = models.BooleanField()

    def __str__(self):
        return str(self.id)

    def redefine_all_records(self, new_item):
        for record in self.records_set.all():
            record.change_item(new_item)
