from openapi_client import AbstractFieldValue, TableFieldValue, WikiTextFieldValue

from apis.cb_client.cb_api_client import CBApiClient
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
                    break

            test_step_fields = self.cb_api_client.tracker_api_instance.get_tracker_field(self.test_case_tracker_id,
                                                                                         test_step_field_id)
            for column in getattr(test_step_fields, "columns"):
                if column.name == "Action":
                    action_field_id = column.id
                if column.name == "Expected result":
                    expected_result_id = column.id

            existing_test_steps = None
            for field in tracker_item.custom_fields:
                if field.field_id == test_step_field_id:
                    existing_test_steps = field
                    break

            # --- ensure we have a TableFieldValue instance ---
            if isinstance(existing_test_steps, TableFieldValue):
                test_steps = existing_test_steps
            else:
                # If it came back as AbstractFieldValue (polymorphism not resolved),
                # rebuild as TableFieldValue from its dumped dict (keeps any existing values)
                if existing_test_steps is not None:
                    test_steps = TableFieldValue.model_validate(existing_test_steps.model_dump(by_alias=True))
                else:
                    test_steps = TableFieldValue(field_id=test_step_field_id, type="TableFieldValue", values=[])
                    tracker_item.custom_fields.append(test_steps)

            test_steps.values = []

            for step in new_steps:
                action = WikiTextFieldValue(field_id=action_field_id, type="WikiTextFieldValue", value=step.action)
                expected = WikiTextFieldValue(field_id=expected_result_id, type="WikiTextFieldValue",
                                              value=step.expected_result)

                test_steps.values.append([action, expected])

            self.cb_api_client.tracker_item_api_instance.update_tracker_item(test_case_id, tracker_item)


if __name__ == "__main__":
    # Input data
    product = "Racecar"
    project_id = 47
    tracker_id = 118107
    test_case_item_ids = [1025787]
    cb_client = CBApiClient("https://pp-26012119166h.portal.ptc.io:9443/cb", "pat", "ptc")

    # Create an instance of TopLevelItemGenerator
    generator = TestStepGenerator(cb_client, product, tracker_id, test_case_item_ids)

    # Call the generate method
    generator.generate()
