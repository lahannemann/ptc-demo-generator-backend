import random

from openapi_client import CreateTestRunRequest, UpdateTestCaseRunRequest, UpdateTestRunRequest

from apis.cb_client.cb_api_client import CBApiClient
from apis.cb_client.utils import Utils


class TestRunGenerator:

    def __init__(self, cb_client, test_case_tracker_id, test_case_items, test_run_tracker_id, passed_count, failed_count, blocked_count):
        self.test_case_tracker_id = test_case_tracker_id
        self.test_run_tracker_id = test_run_tracker_id
        self.passed_count = passed_count
        self.failed_count = failed_count
        self.blocked_count = blocked_count
        self.cb_client = cb_client
        self.test_case_items = test_case_items

    def generate(self):
        test_run = CreateTestRunRequest()
        test_run.test_case_ids = self.test_case_items
        test_run.test_case_refs = self.test_case_items
        test_run.run_only_accepted_test_cases = False

        test_run = self.cb_client.test_run_api_instance.create_test_run_for_test_case(
            self.test_run_tracker_id, test_run)

        result_distribution = ["PASSED"] * self.passed_count + ["FAILED"] * self.failed_count + ["BLOCKED"] * self.blocked_count

        random.shuffle(result_distribution)

        result_list = []
        for test_case, result in zip(self.test_case_items, result_distribution):

            update_result_request = UpdateTestCaseRunRequest(
                result=result,
                testCaseReference=Utils.create_tracker_item_reference_object(test_case.id)
            )

            result_list.append(update_result_request)

        update_result = UpdateTestRunRequest(
            parent_result_propagation=True,
            update_request_models=result_list
        )

        print("Creating test run...")

        self.cb_client.test_run_api_instance.update_test_run_result(test_run.id, update_result)


if __name__ == "__main__":
    # Input data
    project_id = 57
    test_case_tracker_id = 149499
    test_run_tracker_id = 149502
    passed_percent = 55
    failed_percent = 25
    blocked_percent = 5
    cb_client = CBApiClient()

    # Create an instance of ComplianceGenerator
    generator = TestRunGenerator(cb_client, project_id, test_case_tracker_id, test_run_tracker_id, passed_percent, failed_percent, blocked_percent)

    # Call the generate method
    generator.generate()
