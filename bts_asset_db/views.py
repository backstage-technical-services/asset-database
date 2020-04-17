from django.shortcuts import render
from django.template.loader import render_to_string
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Q
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
    context = {'form': ItemForm()}
    return render(request, 'bts_asset_db/record.html', context)


def get_tests(request):
    if request.method == "GET":
        record_id = request.GET.get("record")
        record = Records.objects.get(pk=record_id)
        tests = [list(record.tests_set.all())]
        data = {'tests_rendered': render_to_string('bts_asset_db/partials/record/tests_table.html',
                                                   {'records': [record], 'tests': tests})}
        return JsonResponse(data, safe=False)


def get_records(request):
    if request.method == "GET":
        search_type = request.GET.get('search_type')
        search_query = request.GET.get('search_query')

        if search_type == "item_id":
            filter_functions = [Q(item_id=search_query)]
        elif search_type == "string_data":
            tokens = tokenise_search(search_query)
            filter_functions = [Q(itemmake__make__icontains=token) |
                                Q(itemmodel__model__icontains=token) |
                                Q(itemdescription__asset_description__icontains=token) |
                                Q(itemgroup__asset_group__icontains=token) |
                                Q(itemnotes__notes__icontains=token) |
                                Q(itemserialnumber__serial_number__icontains=token)
                                for token in tokens]
        else:
            filter_functions = Q(item_id=None)

        if filter_functions:
            records = Records.objects.all()
            for filter_function in filter_functions:
                qs = Records.objects.filter(filter_function)
                records &= qs
        else:
            records = Records.objects.none()

        # tests = [list(x.tests_set.all()) for x in records]
        data = dict()
        data['records_rendered'] = render_to_string('bts_asset_db/partials/record/partial_records_body.html',
                                                    {'records': records})
        # data['tests_rendered'] = render_to_string('bts_asset_db/partials/record/tests_table.html',
        #                                           {'records': records, 'tests': tests})
        return JsonResponse(data, safe=False)

    else:
        return index(request)


def visual(request):
    context = {'visual_submit_form': VisualAddForm(auto_id="v_%s"),
               'repair_submit_form': RepairAddForm(auto_id="r_%s"),
               'search_form': VisualSearchForm()}

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

            VisualTests(tester=tester, item=item, supervisor=supervisor,
                        notes=notes, timestamp=timestamp, failed=failed).save()

            new_form = VisualAddForm({'tester': tester, 'supervisor': supervisor},
                                     error_class=MuteErrorList,
                                     auto_id="v_%s")

            message_text = f"Successfully added item {item}"
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

            Repairs(repairer=repairer, item=item, supervisor=supervisor,
                    notes=notes, timestamp=timestamp, failed=failed).save()

            new_form = RepairAddForm({'repairer': repairer, 'supervisor': supervisor},
                                     error_class=MuteErrorList,
                                     auto_id="r_%s")

            message_text = f"Successfully added item {item}"
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

        if search_type == "item_id":
            filter_function = Q(item_id=search_query)
        elif search_type == "tester_id":
            filter_function = Q(tester__first_name__icontains=search_query) | \
                              Q(tester__last_name__icontains=search_query)
        elif search_type == "supervisor_id":
            filter_function = Q(supervisor__first_name__icontains=search_query) | \
                              Q(supervisor__last_name__icontains=search_query)
        elif search_type == "repairer_id":
            filter_function = Q(repairer__first_name__icontains=search_query) | \
                              Q(repairer__first_name__icontains=search_query)
        else:
            filter_function = Q(item_id=None)

        visual_results = VisualTests.objects.filter(filter_function)
        repair_results = Repairs.objects.filter(filter_function)

        records = list(visual_results) + list(repair_results)
        data = {'records_rendered': render_to_string('bts_asset_db/partials/visual/partial_visual_records_body.html',
                                                     {'records': records})}
        return JsonResponse(data, safe=False)


def update_visual_note(request, vis_id):
    if request.user.is_authenticated and request.user.has_perm('bts_asset_db.change_visualtests'):
        if request.method == 'POST':
            new_note_value = request.POST.get('new_value')
            v_test = VisualTests.objects.get(pk=vis_id)
            v_test.notes = new_note_value
            v_test.save()
            return HttpResponse(status=201)
    else:
        return HttpResponse(status=403)
