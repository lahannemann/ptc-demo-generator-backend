from openapi_client import AbstractFieldValue

from apis.gpt_client.gpt_api_client import GPTAPIClient
from apis.gpt_client.gpt_response_data import TestStepParser


class TestStepGenerator:
    def __init__(self, cb_api_client, product, test_case_tracker_id, test_case_item_ids):
        self.cb_api_client = cb_api_client
        self.product = product
        self.test_case_tracker_id = test_case_tracker_id
        self.test_case_item_ids = test_case_item_ids

    def generate(self):
        for test_case_id in self.test_case_item_ids:
            tracker_item = self.cb_api_client.tracker_item_api_instance.get_tracker_item(test_case_id)

            gpt_client = GPTAPIClient()

            # Gets test steps from gpt
            response = gpt_client.get_test_steps(self.product, tracker_item.name)

            parser = TestStepParser(response)
            new_steps = parser.get_items()

            test_step_field_id = None
            action_field_id = None
            expected_result_id = None
            tracker_fields = self.cb_api_client.tracker_api_instance.get_tracker_fields(self.test_case_tracker_id)
            for field in tracker_fields:
                if field.name == "Test Steps":
                    test_step_field_id = field.id

            test_step_fields = self.cb_api_client.tracker_api_instance.get_tracker_field(self.test_case_tracker_id, test_step_field_id)
            for column in getattr(test_step_fields, "columns"):
                if column.name == "Action":
                    action_field_id = column.id
                if column.name == "Expected result":
                    expected_result_id = column.id

            existing_test_steps = None
            for field in tracker_item.custom_fields:
                if field.field_id == test_step_field_id:
                    existing_test_steps = field

            test_steps = None
            if existing_test_steps is not None:
                test_steps = existing_test_steps
            else:
                test_steps = AbstractFieldValue(
                    field_id=test_step_field_id,
                    type="TableFieldValue"
                )
                tracker_item.custom_fields.append(test_steps)

            setattr(test_steps, "values", [])

            for step in new_steps:
                action = AbstractFieldValue(
                    field_id=action_field_id,
                    type="WikiTextFieldValue"
                )
                setattr(action, "value", step.action)

                expected_result = AbstractFieldValue(
                    field_id=expected_result_id,
                    type="WikiTextFieldValue"
                )
                setattr(expected_result, "value", step.expected_result)

                current_values = getattr(test_steps, "values")  # Retrieve the current list
                current_values.append([action, expected_result])  # Append new pair
                setattr(test_steps, "values", current_values)

            self.cb_api_client.tracker_item_api_instance.update_tracker_item(test_case_id, tracker_item)
