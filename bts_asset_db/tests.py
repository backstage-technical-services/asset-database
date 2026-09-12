from django.test import TestCase

from django.urls import reverse
from django.utils import timezone

from .models import Item, Record, Tester, TestingMachine


class LeaderboardViewTests(TestCase):
	def test_leaderboard_ranks_active_testers_by_record_count(self):
		top_tester = Tester.objects.create(
			first_name='Top', last_name='Tester', initials='TOP', pat_level=1, vis_level=1
		)
		other_tester = Tester.objects.create(
			first_name='Other', last_name='Tester', initials='OTH', pat_level=1, vis_level=1
		)
		archived_tester = Tester.objects.create(
			first_name='Archived', last_name='Tester', initials='ARC', pat_level=1, vis_level=1,
			archived=True
		)
		item = Item.objects.create(asset_id='ITEM-1')
		machine = TestingMachine.objects.create(serial_number='MACHINE-1')

		record_data = {
			'item': item,
			'timestamp': timezone.now(),
			'site': 'Site',
			'location': 'Location',
			'testcode_1': 'TEST-1',
			'testcode_2': 'TEST-2',
			'machine_serial_no': machine,
			'machine_firmware_version': '1.0',
			'retest_freq_months': 12,
			'user_data_input_order': 'ORDER-1',
		}

		Record.objects.create(tester=top_tester, **record_data)
		Record.objects.create(tester=top_tester, **record_data)
		Record.objects.create(tester=other_tester, **record_data)
		Record.objects.create(tester=archived_tester, **record_data)

		response = self.client.get(reverse('bts_asset_db:leaderboard'))

		self.assertEqual(response.status_code, 200)
		self.assertEqual(list(response.context['pats']), [top_tester, other_tester])
