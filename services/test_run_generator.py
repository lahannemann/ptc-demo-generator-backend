import random

from openapi_client import CreateTestRunRequest, UpdateTestCaseRunRequest, UpdateTestRunRequest

from apis.cb_client.cb_api_client import CBApiClient
from apis.cb_client.utils import Utils


class TestRunGenerator:

    def __init__(self, cb_client, test_case_tracker_id, item_id_list, test_run_tracker_id, passed_count, failed_count, blocked_count):
        self.test_case_tracker_id = test_case_tracker_id
        self.test_run_tracker_id = test_run_tracker_id
        self.passed_count = passed_count
        self.failed_count = failed_count
        self.blocked_count = blocked_count
        self.cb_client = cb_client
        self.item_id_list = item_id_list

    def generate(self):
        all_test_cases = self.cb_client.get_paginated_tracker_items(self.test_case_tracker_id)
        selected_test_cases = [
            test_case
            for test_case in all_test_cases
            if test_case.id in self.item_id_list
        ]

        test_run = CreateTestRunRequest()
        test_run.test_case_ids = selected_test_cases
        test_run.test_case_refs = selected_test_cases
        test_run.run_only_accepted_test_cases = False

        test_run = self.cb_client.test_run_api_instance.create_test_run_for_test_case(
            self.test_run_tracker_id, test_run)

        result_distribution = ["PASSED"] * self.passed_count + ["FAILED"] * self.failed_count + ["BLOCKED"] * self.blocked_count

        random.shuffle(result_distribution)

        result_list = []
        for test_case, result in zip(selected_test_cases, result_distribution):

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
    test_case_tracker_id = 118107
    test_run_tracker_id = 118110
    selected_ids = [1025791, 1025789]
    passed_percent = 1
    failed_percent = 1
    blocked_percent = 0
    cb_client = CBApiClient("https://pp-26012119166h.portal.ptc.io:9443/cb", "pat", "ptc")

    # Create an instance of ComplianceGenerator
    generator = TestRunGenerator(cb_client, test_case_tracker_id, selected_ids, test_run_tracker_id, passed_percent, failed_percent, blocked_percent)

    # Call the generate method
    generator.generate()
