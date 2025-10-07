from apis.cb_client.cb_api_client import CBApiClient
from apis.cb_client.utils import Utils
from apis.gpt_client.gpt_api_client import GPTAPIClient
from apis.gpt_client.gpt_response_data import ItemsParser


class TraceabilityGenerator:

    def __init__(self, cb_client, product, project_id, upstream_tracker_id, upstream_items, downstream_tracker_id, downstream_count, additional_rules):
        self.product = product
        self.project_id = project_id
        self.upstream_tracker_id = upstream_tracker_id
        self.upstream_items = upstream_items
        self.downstream_tracker_id = downstream_tracker_id
        self.cb_client = cb_client
        self.downstream_count = downstream_count
        self.additional_rules = additional_rules

    def generate(self):
        # Initialize gpt client
        gpt_client = GPTAPIClient()

        # Get upstream tracker information from id
        upstream_tracker = self.cb_client.tracker_api_instance.get_tracker(self.upstream_tracker_id)
        upstream_tracker_name = upstream_tracker.name
        upstream_tracker_type = upstream_tracker.type.name

        # test_step_updater = TestStepUpdater(self.cb_client, gpt_client)

        # Get downstream tracker information from id
        downstream_tracker = self.cb_client.tracker_api_instance.get_tracker(self.downstream_tracker_id)
        downstream_tracker_name = downstream_tracker.name
        downstream_tracker_type = downstream_tracker.type.name

        # Create map of upstream items ids and names
        id_name_map = {value: key for key, value in self.upstream_items.items()}

        # Get new downstream items from GPT
        response = gpt_client.get_downstream_items(id_name_map, self.product, downstream_tracker_name,
                                                   upstream_tracker_name,
                                                   upstream_tracker_type, downstream_tracker_type,
                                                   self.downstream_count, self.additional_rules)
        parser = ItemsParser(response)
        new_items = parser.get_items()

        response_items = []

        # Add each item to downstream tracker
        for item in new_items:
            upstream_reference = Utils.get_abstract_reference_tracker_item(item.parent_id)

            new_added_item = self.cb_client.create_generic_tracker_item(
                downstream_tracker_name, item.name, item.description, upstream_reference)
            response_items.append(new_added_item)


if __name__ == "__main__":
    # Input data
    product = "Racecar"
    project_id = 55
    upstream_tracker_id = 144642
    downstream_tracker_id = 122345
    percent = 100
    cb_client = CBApiClient()
    cb_client.populate_project_data(project_id)

    # Create an instance of TraceabilityGenerator
    generator = TraceabilityGenerator(cb_client, product, project_id, upstream_tracker_id, downstream_tracker_id, percent, 1, 0)

    # Call the generate method
    generator.generate()
