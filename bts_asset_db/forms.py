from django.forms import *
from django.forms.utils import ErrorList
from django.core.exceptions import ObjectDoesNotExist
from .models import VisualTest, Item, Repair, Tester, TestingMachine


class MuteErrorList(ErrorList):
    def __str__(self):
        return ""


class MachineChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.serial_number


class ItemForm(Form):
    options = (('item_id', 'Item ID'),
               ('string_data', 'String Data'))
    search_type = ChoiceField(label='Search Category',
                              choices=options,
                              widget=Select(attrs={'class': 'custom-select'}))
    search_field = CharField(max_length=20,
                             required=False,
                             widget=TextInput(attrs={'class': 'form-control'}))
    tester = ModelChoiceField(queryset=Tester.objects.order_by('last_name', 'first_name'),
                              required=False,
                              empty_label='Any tester',
                              widget=Select(attrs={'class': 'custom-select'}))
    machine = MachineChoiceField(queryset=TestingMachine.objects.order_by('serial_number'),
                                 required=False,
                                 empty_label='Any machine',
                                 widget=Select(attrs={'class': 'custom-select'}))
    passed = ChoiceField(label='Passed',
                         required=False,
                         choices=(('', 'Any result'), ('yes', 'Passed'), ('no', 'Failed')),
                         widget=Select(attrs={'class': 'custom-select'}))
    location = CharField(max_length=15,
                         required=False,
                         widget=TextInput(attrs={'class': 'form-control', 'placeholder': 'Any location'}))
    timestamp_from = DateTimeField(required=False,
                                   input_formats=['%Y-%m-%dT%H:%M'],
                                   widget=DateTimeInput(format='%Y-%m-%dT%H:%M',
                                                        attrs={'class': 'form-control', 'type': 'datetime-local'}))
    timestamp_to = DateTimeField(required=False,
                                 input_formats=['%Y-%m-%dT%H:%M'],
                                 widget=DateTimeInput(format='%Y-%m-%dT%H:%M',
                                                      attrs={'class': 'form-control', 'type': 'datetime-local'}))


class VisualAddForm(ModelForm):
    minor_repair_undertaken = BooleanField(widget=CheckboxInput(attrs={'class': 'custom-control-input'}),
                                           required=False)
    item = CharField(max_length=20,
                     widget=TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = VisualTest
        fields = ['tester', 'item', 'supervisor', 'notes', 'failed']
        widgets = {'tester': Select(attrs={'class': 'custom-select'}),
                   'supervisor': Select(attrs={'class': 'custom-select'}),
                   'notes': TextInput(attrs={'class': 'form-control'}),
                   'failed': CheckboxInput(attrs={'class': 'custom-control-input'})}

    def clean_item(self):
        data = self.cleaned_data['item']

        try:
            result = Item.objects.get(asset_id=data)
        except ObjectDoesNotExist:
            result = Item(asset_id=data)
            result.save()

        return result


class RepairAddForm(ModelForm):
    item = CharField(max_length=20,
                     widget=TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = Repair
        fields = ['repairer', 'item', 'supervisor', 'notes', 'failed']
        widgets = {'repairer': Select(attrs={'class': 'custom-select'}),
                   'supervisor': Select(attrs={'class': 'custom-select'}),
                   'notes': TextInput(attrs={'class': 'form-control'})}

    def clean_item(self):
        data = self.cleaned_data['item']

        try:
            result = Item.objects.get(asset_id=data)
        except ObjectDoesNotExist:
            result = Item(asset_id=data)
            result.save()

        return result


class VisualSearchForm(Form):
    options = (('item_id', 'Item ID'),
               ('tester_id', 'Tester'),
               ('supervisor_id', 'Supervisor'))

    search_type = ChoiceField(label='Search Category',
                              choices=options,
                              widget=Select(attrs={'class': 'custom-select'}))
    search_field = CharField(max_length=20,
                             widget=TextInput(attrs={'class': 'form-control'}))


class NavBarSearchForm(Form):
    navbar_search = CharField(max_length=20,
                              widget=TextInput(attrs={'class': 'form-control'}))
