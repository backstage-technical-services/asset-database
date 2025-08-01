from traceback import print_exc
from django.shortcuts import render
from django.template.loader import render_to_string
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from django.utils import timezone
from django.core import serializers
from django.db.models import Q, Count
from django.contrib.auth.views import redirect_to_login

from bts_asset_db.importscripts import sss_import
from bts_asset_db.importscripts.sss_errors import ImportJobCancelled, MachineNotFound, TesterNotFound
from bts_asset_db.signals import import_cancelled
from .forms import *
from .models import *
from itertools import chain


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
        if request.user.is_authenticated and request.user.has_perm('bts_asset_db.add_pattest'):
            return func(request, *args, **kwargs)
        else:
            return redirect_to_login(
                request.get_full_path(),
                reverse('admin:login', current_app="bts_asset_db")
            )
    return wrapper

   
def import_check_job_state(request, state):
    jobs_state = ImportJob.objects.filter(status=state)
    
    if jobs_state.exists():
        job = jobs_state.first()

        job.processed_percentage = round(job.processed_records / job.total_records * 100)
        return job
    


def import_home(request):
    context = {'navbar_search': NavBarSearchForm()}
    context["state"] = "ready"
    context["jobs"] = ImportJob.objects.order_by('-start_timestamp')[:25]
    

    running_job = import_check_job_state(request, "running")
    if running_job:
        context["state"] = "running"
        context['job'] = running_job
        context["msg_general"] = f'Job {running_job.id} is currently running. Please wait before starting another.'
        return render(request, "bts_asset_db/import.html", context)

    return render(request, "bts_asset_db/import.html", context)
    

def import_upload(request):
    # TODO: Validate file extension
    # TODO: Check if filename already exists in the database, and warn user
    # TODO: cancelled by? probably not necessary
    context = {'navbar_search': NavBarSearchForm(), 'state': 'running'}
    if request.method == 'POST':
        running_job = import_check_job_state(request, "running")
        if running_job:
            context["state"] = "running"
            context['job'] = running_job
            context["msg_error"] = f'Job {running_job.id} is currently running. Please wait before starting another.'
            return render(request, "bts_asset_db/import.html", context)

        upload = request.FILES.get('file')
       
        job = ImportJob.objects.create(
            user=request.user,
            filename=upload.name
        )

        if not upload.name.endswith('.sss'):
            context["state"] = "ready"
            context["msg_error"] = f'File {upload.name} is not a valid SSS file. Please upload a valid SSS file.'
            return render(request, "bts_asset_db/import.html", context)

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
            ImportJob.objects.filter(state="running").first().fail(e)

        job = ImportJob.objects.get(id=job.id)
        context['job'] = job
        if job.status == "completed":
            context["state"] = "completed"
            context["msg_general"] = f"Job {job.id} completed successfully"

        context["job"].processed_percentage = round(context["job"].processed_records / context["job"].total_records * 100)
        
        
        return render(request, "bts_asset_db/import.html", context)
    else:
        return HttpResponse(status=405)

def import_cancel(request):
    context = {'navbar_search': NavBarSearchForm(), 'state': 'failed'}
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
            data['processed_records'] = last_job.processed_records
            data['processed_percentage'] = round(last_job.processed_records / last_job.total_records * 100) if last_job.total_records > 0 else 0
            data['total_records'] = last_job.total_records
            data['error_message'] = last_job.error_message or ''
        else:
            data['status'] = 'ready'
        return JsonResponse(data)
            

        
        