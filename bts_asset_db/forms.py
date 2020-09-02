from django.forms import *
from django.forms.utils import ErrorList
from django.core.exceptions import ObjectDoesNotExist
from .models import VisualTest, Item, Repair


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
        model = VisualTest
        fields = ['tester', 'item', 'supervisor', 'notes', 'failed']
        widgets = {'tester': Select(attrs={'class': 'custom-select'}),
                   'item': TextInput(attrs={'class': 'form-control'}),
                   'supervisor': Select(attrs={'class': 'custom-select'}),
                   'notes': TextInput(attrs={'class': 'form-control'}),
                   'failed': CheckboxInput(attrs={'class': 'custom-control-input'})}

    def clean_item_id(self):
        data = self.cleaned_data['item']

        try:
            result = Item.objects.get(asset_id=data)
        except ObjectDoesNotExist:
            result = Item(asset_id=data)
            result.save()

        return result


class RepairAddForm(ModelForm):
    class Meta:
        model = Repair
        fields = ['repairer', 'item', 'supervisor', 'notes', 'failed']
        widgets = {'repairer': Select(attrs={'class': 'custom-select'}),
                   'item': TextInput(attrs={'class': 'form-control'}),
                   'supervisor': Select(attrs={'class': 'custom-select'}),
                   'notes': TextInput(attrs={'class': 'form-control'}),
                   'failed': CheckboxInput(attrs={'class': 'custom-control-input'})}

    def clean_item_id(self):
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