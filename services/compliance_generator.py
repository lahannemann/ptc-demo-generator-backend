from apis.cb_client.cb_api_client import CBApiClient
from apis.gpt_client.gpt_api_client import GPTAPIClient
from apis.gpt_client.gpt_response_data import ItemsParser


class ComplianceGenerator:

    def __init__(self, cb_client, project_id, tracker_id):
        self.project_id = project_id
        self.tracker_id = tracker_id
        self.cb_client = cb_client

    def generate(self):
        # Initialize gpt client
        gpt_client = GPTAPIClient()

        # Get upstream tracker information from id
        tracker = self.cb_client.tracker_api_instance.get_tracker(self.tracker_id)
        tracker_name = tracker.name
        tracker_type = tracker.type.name

        # Get new downstream items from GPT
        response = gpt_client.get_compliance_top_level(tracker_name, tracker_type)

        # Parses new items into objects
        parser = ItemsParser(response)
        new_items = parser.get_items()

        # Add each item to tracker
        for item in new_items:
            self.cb_client.create_generic_tracker_item(
                tracker_name, item.name, item.description, None)


if __name__ == "__main__":
    # Input data
    project_id = 24
    tracker_id = 68981
    cb_client = CBApiClient()
    cb_client.populate_project_data(project_id)

    # Create an instance of ComplianceGenerator
    generator = ComplianceGenerator(cb_client, project_id, tracker_id, 0)

    # Call the generate method
    generator.generate()
