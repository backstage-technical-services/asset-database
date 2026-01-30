import logging
from io import BytesIO

from django.dispatch import receiver

from bts_asset_db.importscripts.sss_errors import ImportJobCancelled, MachineNotFound, TesterNotFound
from .sss_base import *
from bts_asset_db.models import *
from bts_asset_db.signals import import_cancelled
from django.utils.timezone import make_aware
from django.db.models import Q
from django.db import transaction
import datetime

machine_serial = None
job = None
cancelled = False
processed_records = 0

@receiver(import_cancelled)
def import_cancelled_handler(sender, **kwargs):
    logging.info("Import job cancelled signal received")
    global cancelled
    cancelled = True

def sss_import(data):
    global job, cancelled
    cancelled = False
    logging.basicConfig(level=logging.INFO)

    job = ImportJob.objects.filter(status='running').first()
    
    file_contents = BytesIO(data)
    try:
        read_sss(file_contents)
    except SSSSyntaxError as message:
        print('End File {Error:"%s"}' % message)
        
    update_machine_latest_record_times()


def update_machine_latest_record_times():
    for machine in TestingMachine.objects.all():
        try:
            timestamp = Record.objects.filter(machine_serial_no=machine).latest('timestamp', 'id').timestamp
        except ObjectDoesNotExist as e:
            timestamp = make_aware(datetime.datetime(1970, 1, 1, 0, 0))

        machine.last_imported_record_time = timestamp
        machine.save()


def read_sss(file_contents):
    global job, machine_serial, processed_records
    records = get_records(file_contents, SSSRecordHeader())
    machine_serial = None
    # duplicates generator
    records = list(records)
    total_records = sum(1 for _ in iter(records))
    ImportJob.objects.filter(status='running').update(
        total_records=total_records
    )       

    records = iter(records)

    processed_records = 0
    try:
        with transaction.atomic():
            while True:
                if cancelled:
                    logging.info("Import job cancelled, rolling back transaction")
                    raise ImportJobCancelled()
                try:
                    payload = next(records)
                    processed_records += 1
                except StopIteration:
                    # file parsing complete
                    break
                parse_record(payload)


    except TestingMachine.DoesNotExist as e:
        logging.error(f"Testing machine with serial number '{machine_serial}' does not exist: {e}")
        transaction.rollback()
        raise MachineNotFound(machine_serial)

    except Exception as e:
        logging.error(f"Error processing record: {e}")
        transaction.rollback()
        raise e
    
    finally:
        ImportJob.objects.filter(id=job.id).update(
            processed_records=processed_records,
        )
        if machine_serial:
            ImportJob.objects.filter(id=job.id).update(
                machine=TestingMachine.objects.get(serial_number=machine_serial)
            )


    updated_job = ImportJob.objects.filter(id=job.id).first()
    if updated_job.status != 'running':
        logging.error(f"Import job status changed unexpectedly: {updated_job.status}")
        transaction.rollback()
    if processed_records == total_records:
        ImportJob.objects.filter(status='running').first().complete()
        transaction.commit()
    else:
        transaction.rollback()


def get_records(file_contents, record_header):
    # Retrieve and validate records
    while True:
        header = file_contents.read(len(record_header))

        if not header:
            # we've hit the end of the file, stop now
            break

        record_header.unpack(header)

        if record_header.data['payload_length'] == 0:
            logging.warning('Zero length payload for a record')
            continue

        payload = file_contents.read(record_header.data['payload_length'])

        if not record_header.checksum(payload):
            logging.error('Checksum validation failed for a record')
            continue

        yield payload


def parse_record(payload):
    record = Record()
    tests = TESTS_VERSION_1.copy()
    version = 1

    test_type = None
    entries_to_create = []

    while payload and test_type != 0xff:
        test_type = payload[0]
        # Add in newer-style records if detected by presence of 0x11/0x12
        if version == 1 and test_type in (0x11, 0x12):
            version += 1
            tests.update(TESTS_VERSION_2)

        payload = payload[1:]

        # Unpack the current sub-field
        current_test = tests[test_type][1]()
        current_test.unpack(payload[:len(current_test)])
        entries_exported = export_record(record, current_test.data, test_type)
        if entries_exported is not None:
            entries_to_create += entries_exported

        # Seek past to start of next sub-field
        payload = payload[len(current_test):]

    if record.timestamp > (record.machine_serial_no.last_imported_record_time or make_aware(datetime.datetime(1970, 1, 1, 0, 0))):
        if not record.retest_freq_months:
            record.retest_freq_months = 12
        record.save()
        for entry in entries_to_create:
            entry.record = record
            entry.save()


def export_record(record, data, test_type):
    global machine_serial
    test = PatTest(test_type=test_type)
    entities_to_create = []

    if test_type in (0x01, 0x02, 0x11, 0x12):
        # Record a visual test result
        record.testcode_1 = data['testcode1']
        record.testcode_2 = data['testcode2']
        record.site = data['site']
        record.location = data['location']
        try:
            record.tester = Tester.objects.get(Q(machine_name=data['tester']) | Q(alt_machine_name=data['tester']))
        except Tester.DoesNotExist:
            logging.error(f"Tester '{data['tester']}' not found in database. Please add it before importing this record.")
            raise TesterNotFound(data['tester'])
        record.timestamp = make_aware(datetime.datetime(data['year'],
                                             data['month'],
                                             data['day'],
                                             data['hour'],
                                             data['minute']))

        record.item, _ = Item.objects.get_or_create(asset_id=data['id'])

    elif test_type == 0xe0:
        # User Data Input Order
        record.user_data_input_order = (data['mapping1'], data['mapping2'], data['mapping3'], data['mapping4'])

    elif test_type == 0xe1:
        # Retest Frequency
        record.retest_freq_months = data['frequency']

    elif test_type in range(0xf0, 0xfb):
        # These are individual tests, just lump parameters into one table
        test_params = [round(val, 4) if type(val) == float else val for val in data.values()]
        no_of_params = len(test_params)

        test.test_parameter_1 = test_params[0] if (no_of_params > 0) else None
        test.test_parameter_2 = test_params[1] if (no_of_params > 1) else None
        test.test_parameter_3 = test_params[2] if (no_of_params > 2) else None

        entities_to_create.append(test)

    elif test_type == 0xfb:
        # These are the user data fields. Assume we already have info about the data order.
        user_data = list(data.values())
        mappings = {0: "item_notes",
                    1: "item_description",
                    2: "item_group",
                    3: "item_make",
                    4: "item_model",
                    5: "item_serial_number"}
        
        if machine_serial == "Y49-0892":
            # Unfortunately, this tester is special
            # Backstage stores initials on the 2nd line, which is expected to be item_notes
            # This tester outputs the 2nd line as item_group instead
            mappings[0], mappings[2] = mappings[2], mappings[0]

        # Deals with the fact multiple user_data entries may be of the same type.
        # If this happens, separate with /n.

        for mapping, fieldname in mappings.items():
            contents = [data
                        for ind, data in enumerate(user_data)
                        if record.user_data_input_order[ind] == mapping]
            if contents:
                combined_data = "\n".join(contents).strip()
                if fieldname == "item_notes":
                    try:
                        # Setting tester by initials is a more reliable method. This will overwrite the earlier assignment if a match is found.
                        record.tester = Tester.objects.get(Q(initials=combined_data))
                    except Tester.DoesNotExist:
                        0
                        
                setattr(record, fieldname, combined_data)

    elif test_type == 0xfe:
        # Tester serial number and firmware
        record.machine_serial_no_id = data['serialnumber']
        record.machine_firmware_version = '%d.%d.%d' % (data['firmware1'], data['firmware2'], data['firmware3'])
        machine_serial = data['serialnumber']
    else:
        # Unknown
        # logging.warning("Invalid or unknown type passed: %x" % test_type)
        pass

    return entities_to_create
