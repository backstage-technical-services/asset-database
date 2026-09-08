import os
import subprocess
from itertools import chain
from traceback import print_exc

from django.contrib.auth.views import redirect_to_login
from django.core import serializers
from django.core.paginator import Paginator
from django.db.models import Count, Exists, OuterRef, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from bts_asset_db.importscripts import sss_import
from bts_asset_db.importscripts.sss_errors import (
    ImportJobCancelled,
    MachineNotFound,
    TesterNotFound,
)
from bts_asset_db.signals import import_cancelled

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
        record = Record.objects.select_related('item', 'machine_serial_no').get(pk=record_id)
        tests = [list(record.pattest_set.all())]
        data = {'tests_rendered': render_to_string('bts_asset_db/partials/record/tests_table.html',
                                                   {'records': [record], 'tests': tests})}
        return JsonResponse(data, safe=False)


def get_records(request):
    if request.method == "GET":
        search_type = request.GET.get('search_type')
        search_query = (request.GET.get('search_query') or '').strip()
        tester = request.GET.get('tester')
        machine = request.GET.get('machine')
        passed = request.GET.get('passed')
        location = request.GET.get('location')
        timestamp_from = request.GET.get('timestamp_from')
        timestamp_to = request.GET.get('timestamp_to')
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 25))

        if not search_query or not search_query.strip():
            records = Record.objects.all().order_by('-timestamp')
        elif search_type == "item_id":
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

        if search_query and search_query.strip() and filter_functions:
            records = Record.objects.all().order_by('-timestamp')
            for filter_function in filter_functions:
                qs = Record.objects.filter(filter_function).select_related("tester")
                records &= qs
        elif search_query and search_query.strip():
            records = Record.objects.none()

        if tester:
            records = records.filter(tester_id=tester)
        if machine:
            records = records.filter(machine_serial_no__pk=machine)
        if location:
            records = records.filter(location__icontains=location)
        if timestamp_from:
            records = records.filter(timestamp__gte=timestamp_from)
        if timestamp_to:
            records = records.filter(timestamp__lte=timestamp_to)
        if passed in ('yes', 'no'):
            failed_test = PatTest.objects.filter(record=OuterRef('pk')).filter(
                Q(test_type=241) |
                Q(test_type=242) & (
                    Q(test_parameter_2='False') |
                    (Q(test_parameter_1__isnull=True) &
                     Q(test_parameter_2__isnull=True) &
                     Q(test_parameter_3__isnull=True))
                ) |
                Q(test_type__in=range(243, 249)) &
                (Q(test_parameter_1='False') | Q(test_parameter_1__isnull=True))
            )
            records = records.annotate(has_failed_test=Exists(failed_test))
            records = records.filter(has_failed_test=(passed == 'no'))

        records = records.select_related(
            'item', 'tester', 'machine_serial_no'
        ).prefetch_related('pattest_set')
        records_paginator = Paginator(records, per_page)
        records = records_paginator.get_page(page)
        tests = Paginator([list(x.pattest_set.all()) for x in records], per_page).get_page(page)
        data = dict()

        for record in records:
            record.passed = all(test.passed for test in record.pattest_set.all() if test.passed is not None)

        if search_type == "item_id" and search_query and search_query.strip():
            latest_record = Record.objects.filter(
                item__asset_id=search_query
            ).order_by('-timestamp').prefetch_related('pattest_set').first()
            if latest_record:
                latest_record.passed = all(
                    test.passed for test in latest_record.pattest_set.all()
                    if test.passed is not None
                )
                if latest_record.passed is False:
                    data['msg_warning'] = f"Item {latest_record.item.asset_id} has failed. Please place the item in a quarantine bin"
                # The fixed 12-month threshold follows internal risk assessments;
                # retest_freq_months is currently unused for this warning.
                elif latest_record.timestamp < timezone.now() - timezone.timedelta(days=365):
                    data['msg_warning'] = f"Item {latest_record.item.asset_id} is out of PAT. Please place the item in a quarantine bin"


        data['page'] = page
        data['records_rendered'] = render_to_string('bts_asset_db/partials/record/partial_records_body.html',
                                                    {'records': records, 'page': page})
        data['tests_rendered'] = render_to_string('bts_asset_db/partials/record/tests_table.html',
                                                  {'records': records, 'tests': tests})
        data['pagination_rendered'] = render_to_string('bts_asset_db/partials/record/records_pagination.html',
                                                       {'records': records, 'page': page, 'num_pages': records_paginator.num_pages})
        data['msg_warning_rendered'] = render_to_string('bts_asset_db/partials/record/item_warning.html',
                                                       {'msg_warning': data.get('msg_warning', '')})
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
            minor_repair = form.cleaned_data['minor_repair_undertaken']

            if minor_repair:
                VisualTest(tester=tester, item=item, supervisor=supervisor,
                           notes=notes, timestamp=timestamp, failed=True).save()
                Repair(repairer=tester, item=item, supervisor=supervisor,
                       notes=notes, timestamp=timestamp, failed=failed).save()

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

            Repair(repairer=repairer, item=item, supervisor=supervisor,
                   notes=notes, timestamp=timestamp).save()

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
        visual_records = VisualTest.objects.all().order_by('-timestamp')
        repair_records = Repair.objects.all().order_by('-timestamp')

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
                repair_results = Repair.objects.filter(filter_function).select_related("repairer", "supervisor")

                visual_records &= visual_results
                repair_records &= repair_results
        else:
            visual_records = VisualTest.objects.none()
            repair_records = Repair.objects.none()

        records = sorted(chain(visual_records, repair_records), key=lambda record: record.timestamp, reverse=True)


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
        rendered = render_to_string('bts_asset_db/partials/asset/partial_itemclass_table.html',
                                    {'itemclasses': itemclasses})
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
        # rendered = render_to_string('bts_asset_db/partials/asset/partial_item.html', {'items': item})
        # data = {"rendered": rendered}
        return render(request, 'bts_asset_db/partials/asset/partial_item.html', {'items': item})

def import_auth_wrapper(func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(
                request.get_full_path(),
                reverse('admin:login', current_app="bts_asset_db")
            )
        if not request.user.has_perm('bts_asset_db.add_pattest'):
            return HttpResponse(status=403)
        return func(request, *args, **kwargs)
    
    return wrapper

   
def import_check_job_state(request, state):
    jobs_state = ImportJob.objects.filter(status=state)
    
    if jobs_state.exists():
        job = jobs_state.first()

        try:

            job.processed_percentage = round(job.processed_records / job.total_records * 100)
        except ZeroDivisionError:
            job.processed_percentage = 0
        return job
    


def import_home(request):
    context = {'navbar_search': NavBarSearchForm()}
    context["state"] = "ready"
    context["jobs"] = ImportJob.objects.order_by('-start_timestamp')[:50]
    

    running_job = import_check_job_state(request, "running")
    if running_job:
        context["state"] = "running"
        context['job'] = running_job
        context["msg_general"] = f'Job {running_job.id} is currently running. Please wait before starting another.'
        return render(request, "bts_asset_db/import.html", context)

    return render(request, "bts_asset_db/import.html", context)
    

def import_upload(request):
    context = {'navbar_search': NavBarSearchForm(), 'state': 'running'}
    context["jobs"] = ImportJob.objects.order_by('-start_timestamp')[:25]
    if request.method == 'POST':
        running_job = import_check_job_state(request, "running")
        if running_job:
            context["state"] = "running"
            context['job'] = running_job
            context["msg_error"] = f'Job {running_job.id} is currently running. Please wait before starting another.'
            return render(request, "bts_asset_db/import.html", context)

        upload = request.FILES.get('file')
       
        if not upload.name.endswith('.sss'):
            context["state"] = "ready"
            context["msg_error"] = f'File {upload.name} is not a valid SSS file. Please upload a valid SSS file.'
            return render(request, "bts_asset_db/import.html", context)

        previous_job = ImportJob.objects.filter(filename=upload.name, status="completed").first()

        if previous_job:
            context["state"] = "ready"
            context["msg_error"] = f'File {upload.name} was already imported successfully in job {previous_job.id}. Importing the data in this file again will create duplicate records.'
            return render(request, "bts_asset_db/import.html", context)

        backup_file = f'/app/backups/import_backup_{timezone.now().strftime("%Y%m%d_%H%M%S")}.sql'
        try:
            subprocess.run(f'mariadb-dump -u {os.environ["DB_USER"]} --password={os.environ["DB_PASS"]} -h {os.environ["DB_HOST"]} {os.environ["DB_NAME"]} > {backup_file}', shell=True, check=True)
        except subprocess.CalledProcessError as e:
            print_exc()
            context["state"] = "ready"
            e_str = str(e)
            e_str = e_str.replace(os.environ["DB_USER"], "*****")
            e_str = e_str.replace(os.environ["DB_PASS"], "*****")
            context["msg_error"] = f'Import failed to start. Database backup failed: {e_str}'
            return render(request, "bts_asset_db/import.html", context)
        
        backups = sorted(os.listdir('/app/backups/'))
        if len(backups) > 10:
            for backup in backups[:-10]:
                # prevent real backups from being deleted when lots of failed imports happen
                # only cycle a backup if it is older than 7 days
                if os.path.getmtime(f'/app/backups/{backup}') < (timezone.now() - timezone.timedelta(days=7)).timestamp():
                    os.remove(f'/app/backups/{backup}')

        job = ImportJob.objects.create(
            user=request.user,
            filename=upload.name
        )

        job.save()        

        try:
            sss_import.sss_import(upload.read())
        except TesterNotFound as e:
            context["state"] = "failed"
            context["msg_error"] = f'Error during import: The machine references tester \'{e.tester_id}\' which does not exist in the database. Please add the tester before importing.'
            print_exc()
            job.fail(e)
        except MachineNotFound as e:        
            context["state"] = "failed"
            context["msg_error"] = f'Error during import: The machine with serial number \'{e.machine_serial}\' does not exist in the database. Please add the machine before importing.'
            print_exc()
            job.fail(e)
        except ImportJobCancelled as e:
            context["state"] = "cancelled"
            context["msg_error"] = f'Import job was cancelled by another user.'
            print_exc()
        except Exception as e:
            context["state"] = "ready"
            context["msg_error"] = f'Error during import: {e}'
            print_exc()
            ImportJob.objects.filter(status="running").first().fail(e)

        job = ImportJob.objects.get(id=job.id)
        context['job'] = job
        if job.status == "completed":
            context["state"] = "completed"
            context["msg_general"] = f"Job {job.id} completed successfully"

        try:

            context["job"].processed_percentage = round(context["job"].processed_records / context["job"].total_records * 100)

        except ZeroDivisionError:
            context["job"].processed_percentage = 0
        
        
        return render(request, "bts_asset_db/import.html", context)
    else:
        return HttpResponse(status=405)

def import_cancel(request):
    context = {'navbar_search': NavBarSearchForm(), 'state': 'failed'}
    context["jobs"] = ImportJob.objects.order_by('-start_timestamp')[:25]
    if request.method == 'POST':
        running_job = import_check_job_state(request, "running")

        if not running_job:
            context["state"] = "ready"
            context["msg_error"] = f'Unable to cancel job as no job is currently running.'
            context["msg_general"] = ''
            return render(request, "bts_asset_db/import.html", context)

        context["job"] = running_job

        running_job.cancel()

        context["msg_general"] = f'Job {running_job.id} has been cancelled. Please wait while the system rolls back to the previous state.'

        # send signal to job to cancel
        import_cancelled.send(sender=ImportJob, job=running_job)

        return render(request, "bts_asset_db/import.html", context)
    else:
        return HttpResponse(status=405)



def import_status(request):
    if request.method == 'GET':        
        last_job = ImportJob.objects.order_by('-start_timestamp').first()
        data = {}
        if last_job:
            data['job_id'] = last_job.id
            data['status'] = last_job.status
            data['start_timestamp'] = last_job.start_timestamp.isoformat()
            data['end_timestamp'] = last_job.end_timestamp.isoformat() if last_job.end_timestamp else None
            data['processed_records'] = sss_import.processed_records
            try:
                data['processed_percentage'] = round(sss_import.processed_records / last_job.total_records * 100) if last_job.total_records > 0 else 0
            except ZeroDivisionError:
                data['processed_percentage'] = 0
            data['total_records'] = last_job.total_records
            data['error_message'] = last_job.error_message or ''
        else:
            data['status'] = 'ready'
        return JsonResponse(data)
            

        
        