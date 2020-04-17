from django.forms import *
from django.forms.utils import ErrorList
from django.core.exceptions import ObjectDoesNotExist
from .models import VisualTests, Item, Repairs


class MuteErrorList(ErrorList):
    def __str__(self):
        return ""


class ItemForm(Form):
    options = (('item_id', 'Item ID'),
               ('string_data', 'String Data'))
    search_type = ChoiceField(label='Search Category',
                              choices=options,
                              widget=Select(attrs={'class': 'custom-select'}))
    search_field = CharField(max_length=20,
                             widget=TextInput(attrs={'class': 'form-control'}))


class VisualAddForm(ModelForm):
    class Meta:
        model = VisualTests
        fields = ['tester', 'item', 'supervisor', 'notes', 'failed']
        widgets = {'tester': Select(attrs={'class': 'custom-select'}),
                   'item': TextInput(attrs={'class': 'form-control'}),
                   'supervisor': Select(attrs={'class': 'custom-select'}),
                   'notes': TextInput(attrs={'class': 'form-control'}),
                   'failed': CheckboxInput(attrs={'class': 'custom-control-input'})}

    def clean_item_id(self):
        data = self.cleaned_data['item']

        try:
            result = Item.objects.get(pk=data)
        except ObjectDoesNotExist:
            raise ValidationError(
                'Invalid item: %(item)s',
                code='invalid',
                params={'item': data}
            )

        return result


class RepairAddForm(ModelForm):
    class Meta:
        model = Repairs
        fields = ['repairer', 'item', 'supervisor', 'notes', 'failed']
        widgets = {'repairer': Select(attrs={'class': 'custom-select'}),
                   'item': TextInput(attrs={'class': 'form-control'}),
                   'supervisor': Select(attrs={'class': 'custom-select'}),
                   'notes': TextInput(attrs={'class': 'form-control'}),
                   'failed': CheckboxInput(attrs={'class': 'custom-control-input'})}

    def clean_item_id(self):
        data = self.cleaned_data['item']

        try:
            result = Item.objects.get(pk=data)
        except ObjectDoesNotExist:
            raise ValidationError(
                'Invalid item: %(item)s',
                code='invalid',
                params={'item': data}
            )

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