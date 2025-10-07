from apis.cb_client.cb_api_client import CBApiClient
from apis.gpt_client.gpt_api_client import GPTAPIClient
from apis.gpt_client.gpt_response_data import ItemsParser


class TopLevelItemGenerator:

    requirement_types_mapping = {
        "hardware": "The requirements should all be hardware requirements.",
        "software": "The requirements should all be software requirements.",
        "both": "The requirements should be a mix of hardware and software requirements."
    }

    def __init__(self, cb_client, product, tracker_id, item_count, requirement_type, additional_rules):
        self.product = product
        self.tracker_id = tracker_id
        self.item_count = item_count
        self.cb_client = cb_client
        self.requirement_type_prompt_text = self.requirement_types_mapping.get(requirement_type)
        self.additional_rules = additional_rules

    def generate(self):
        # Initialize gpt client
        gpt_client = GPTAPIClient()

        # Get tracker information from id
        tracker = self.cb_client.tracker_api_instance.get_tracker(self.tracker_id)
        tracker_name = tracker.name
        tracker_type = tracker.type.name

        # test_step_updater = TestStepUpdater(self.cb_client, gpt_client)

        # Get new top level items from GPT
        response = gpt_client.get_top_level_items(self.product, tracker_name, tracker_type, self.item_count, self.requirement_type_prompt_text, self.additional_rules)

        parser = ItemsParser(response)
        new_items = parser.get_items()

        response_items = []

        # Add each item to tracker
        for item in new_items:
            new_added_item = self.cb_client.create_generic_tracker_item(
                self.tracker_id, item.name, item.description, None)
            response_items.append(new_added_item)

        # if tracker_type == "Testcase":
        #     test_step_updater.update_test_steps(self.product, self.tracker_id, response_items)


if __name__ == "__main__":
    # Input data
    product = "Racecar"
    project_id = 24
    tracker_id = 68977
    item_count = 1
    cb_client = CBApiClient()
    cb_client.populate_project_data(project_id)

    # Create an instance of TopLevelItemGenerator
    generator = TopLevelItemGenerator(cb_client, product, tracker_id, item_count, 0, "Hardware Requirements")

    # Call the generate method
    generator.generate()
