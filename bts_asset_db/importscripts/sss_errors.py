from bts_asset_db.models import Tester, TestingMachine


class TesterNotFound (Tester.DoesNotExist):
    """Raised when a tester is not found in the database."""
    def __init__(self, tester_id):
        self.tester_id = tester_id
        super().__init__(f"Tester with ID {tester_id} not found in the database.")

class MachineNotFound (TestingMachine.DoesNotExist):
    """Raised when a machine is not found in the database."""
    def __init__(self, machine_serial):
        self.machine_serial = machine_serial
        super().__init__(f"Testing machine with serial number {machine_serial} not found in the database.")

class ImportJobCancelled(Exception):
    """Raised when an import job is interrupted by a cancellation."""
    def __init__(self, message="Import job was cancelled by another user."):
        super().__init__(message)