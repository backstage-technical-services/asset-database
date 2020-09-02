import json
from django.shortcuts import render
from django.template.loader import render_to_string
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.core import serializers
from django.core.serializers.json import DjangoJSONEncoder
from django.db import connection, connections
from django.db.models import Q, F, Count
from .forms import *
from .models import *


def tokenise_search(search_query):
    if "'" in search_query and (search_query.count("'") % 2 == 0):
        tokens = []
        subs = search_query.split("'")
        tokens += subs[1::2]  # Take all odd elems, ie elems within apostrophes, add to tokens
        other_tokens_not_flat = [x.split() for x in subs[::2]]  # Take all even elems and split each of them
        tokens += [item for sublist in other_tokens_not_flat for item in sublist]  # Flatten and append
    else:
        tokens = search_query.split()

    return tokens


def index(request):
    context = {'form': ItemForm(),
               'navbar_search': NavBarSearchForm()}
    return render(request, 'bts_asset_db/record.html', context)


def get_tests(request):
    if request.method == "GET":
        record_id = request.GET.get("record")
        record = Record.objects.select_related('item').get(pk=record_id)
        tests = [list(record.pattest_set.all())]
        data = {'tests_rendered': render_to_string('bts_asset_db/partials/record/tests_table.html',
                                                   {'records': [record], 'tests': tests})}
        return JsonResponse(data, safe=False)


def get_records(request):
    if request.method == "GET":
        search_type = request.GET.get('search_type')
        search_query = request.GET.get('search_query')

        if search_type == "item_id":
            filter_functions = [Q(item__asset_id=search_query)]
        elif search_type == "string_data":
            tokens = tokenise_search(search_query)
            filter_functions = [Q(item_make__icontains=token) |
                                Q(item_model__icontains=token) |
                                Q(item_description__icontains=token) |
                                Q(item_group__icontains=token) |
                                Q(item_notes__icontains=token) |
                                Q(item_serial_number__icontains=token)
                                for token in tokens]
        else:
            filter_functions = Q(item_id=None)

        if filter_functions:
            records = Record.objects.all().order_by('-timestamp')
            for filter_function in filter_functions:
                qs = Record.objects.filter(filter_function).select_related("tester")
                records &= qs
        else:
            records = Record.objects.none()

        tests = [list(x.pattest_set.all()) for x in records]
        data = dict()
        data['records_rendered'] = render_to_string('bts_asset_db/partials/record/partial_records_body.html',
                                                    {'records': records})
        data['tests_rendered'] = render_to_string('bts_asset_db/partials/record/tests_table.html',
                                                   {'records': records, 'tests': tests})
        return JsonResponse(data, safe=False)

    else:
        return index(request)


def visual(request):
    context = {'visual_submit_form': VisualAddForm(auto_id="v_%s"),
               'repair_submit_form': RepairAddForm(auto_id="r_%s"),
               'search_form': VisualSearchForm(),
               'navbar_search': NavBarSearchForm()}

    # TODO: Add authentication again:
    #  if request.user.is_authenticated and
    #  request.user.has_perm('bts_asset_db.add_visualtests'):
    if request.method == 'POST' and "visual-submit" in request.POST:
        # create a form instance and populate it with data from the request:
        form = VisualAddForm(request.POST, error_class=MuteErrorList, auto_id="v_%s")
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            tester = form.cleaned_data['tester']
            item = form.cleaned_data['item']
            supervisor = form.cleaned_data['supervisor']
            notes = form.cleaned_data['notes']
            timestamp = timezone.now()
            failed = form.cleaned_data['failed']

            VisualTest(tester=tester, item=item, supervisor=supervisor,
                       notes=notes, timestamp=timestamp, failed=failed).save()

            new_form = VisualAddForm({'tester': tester, 'supervisor': supervisor},
                                     error_class=MuteErrorList,
                                     auto_id="v_%s")

            message_text = f"Successfully added visual record for item {item}"
            if not item.processed:
                message_text = message_text + " and created new item in database"

            context['visual_submit_form'] = new_form
            context['msg_general'] = message_text
        else:
            message_text = form.errors['item'][0]
            context['visual_submit_form'] = form
            context['msg_error'] = message_text

    elif request.method == 'POST' and "repair-submit" in request.POST:
        # create a form instance and populate it with data from the request:
        form = RepairAddForm(request.POST, error_class=MuteErrorList, auto_id="r_%s")
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            repairer = form.cleaned_data['repairer']
            item = form.cleaned_data['item']
            supervisor = form.cleaned_data['supervisor']
            notes = form.cleaned_data['notes']
            timestamp = timezone.now()
            failed = form.cleaned_data['failed']

            Repair(repairer=repairer, item=item, supervisor=supervisor,
                   notes=notes, timestamp=timestamp, failed=failed).save()

            new_form = RepairAddForm({'repairer': repairer, 'supervisor': supervisor},
                                     error_class=MuteErrorList,
                                     auto_id="r_%s")

            message_text = f"Successfully added repair record for item {item}"
            if not item.processed:
                message_text = message_text + " and created new item in database"

            context['repair_submit_form'] = new_form
            context['msg_general'] = message_text
        else:
            message_text = form.errors['item'][0]
            context['repair_submit_form'] = form
            context['msg_error'] = message_text

    # if a GET (or any other method) we'll create a blank form
    return render(request, "bts_asset_db/visual.html", context)


def get_visuals(request):
    if request.method == 'GET':
        search_type = request.GET.get("search_type")
        search_query = request.GET.get("search_query")

        tokens = tokenise_search(search_query)
        records = VisualTest.objects.all().order_by('-timestamp')
        if tokens:
            for token in tokens:
                if search_type == "item_id":
                    filter_function = Q(item__asset_id=token)
                elif search_type == "tester_id":
                    filter_function = Q(tester__first_name__icontains=token) | \
                                      Q(tester__last_name__icontains=token)
                elif search_type == "supervisor_id":
                    filter_function = Q(supervisor__first_name__icontains=token) | \
                                      Q(supervisor__last_name__icontains=token)
                elif search_type == "repairer_id":
                    filter_function = Q(repairer__first_name__icontains=token) | \
                                      Q(repairer__first_name__icontains=token)
                else:
                    filter_function = Q(item_id=None)

                visual_results = VisualTest.objects.filter(filter_function).select_related("tester", "supervisor")
                # repair_results = Repairs.objects.filter(filter_function).select_related("repairer", "supervisor")

                records &= visual_results  # + list(repair_results)
        else:
            records = VisualTest.objects.none()
        data = {'records_rendered': render_to_string('bts_asset_db/partials/visual/partial_visual_records_body.html',
                                                     {'records': records})}
        return JsonResponse(data, safe=False)


def update_visual_note(request, vis_id):
    if request.user.is_authenticated and request.user.has_perm('bts_asset_db.change_visualtests'):
        if request.method == 'POST':
            new_note_value = request.POST.get('new_value')
            v_test = VisualTest.objects.get(pk=vis_id)
            v_test.notes = new_note_value
            v_test.save()
            return HttpResponse(status=201)
    else:
        return HttpResponse(status=403)


def asset_search(request):
    context = {'navbar_search': NavBarSearchForm()}
    return render(request, "bts_asset_db/asset.html", context)


def itemclass_info(request, itemclass_id):
    if request.method == "GET":
        itemclass = ItemClass.objects.get(pk=itemclass_id)
        data = {'rendered': render_to_string('bts_asset_db/partials/asset/partial_itemclass.html',
                                             {'itemclass': itemclass})}

        return JsonResponse(data, safe='False')


def get_departments(request):
    if request.method == "GET":
        departments = Department.objects.all()
        data = serializers.serialize('json', departments)
        return HttpResponse(data, content_type='application/json')


def get_categories(request):
    if request.method == "GET":
        department_id = request.GET.get('department_id')
        categories = Category.objects.filter(department_id=department_id)
        data = serializers.serialize('json', categories)
        return HttpResponse(data, content_type='application/json')


def get_subcategories(request):
    if request.method == "GET":
        category_id = request.GET.get('category_id')
        subcategories = Subcategory.objects.filter(category_id=category_id)
        data = serializers.serialize('json', subcategories)
        return HttpResponse(data, content_type='application/json')


def get_itemclasses(request):
    if request.method == "GET":
        subcategory_id = request.GET.get('subcategory_id')
        itemclasses = ItemClass.objects.filter(subcategory_id=subcategory_id) \
                                       .prefetch_related("member_item_set") \
                                       .annotate(quantity=Count('member_item_set'))
        rendered = render_to_string('bts_asset_db/partials/asset/partial_itemclass_table.html', {'itemclasses': itemclasses})
        data = {"rendered": rendered}
        return JsonResponse(data, safe='False')


def get_item(request, item_id):
    if request.method == "GET":
        item = Item.objects.filter(pk=item_id) \
                           .select_related("itemclass", "owner") \
                           .prefetch_related('record_set', 'record_set__pattest_set')
        rendered = render_to_string('bts_asset_db/partials/asset/partial_item.html', {'items': item})
        data = {"rendered": rendered}
        return JsonResponse(data, safe='False')


def test_get_item(request, item_id):
    if request.method == "GET":
        item = Item.objects.filter(pk=item_id) \
                           .select_related("itemclass", "owner") \
                           .prefetch_related('record_set', 'record_set__pattest_set',
                                             'children_set', 'children_set__record_set',
                                             'children_set__record_set__pattest_set')
        rendered = render_to_string('bts_asset_db/partials/asset/partial_item.html', {'items': item})
        data = {"rendered": rendered}
        return render(request, 'bts_asset_db/partials/asset/partial_item.html', {'items': item})

