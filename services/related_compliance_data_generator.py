import random

from apis.cb_client.cb_api_client import CBApiClient
from apis.cb_client.utils import Utils
from apis.gpt_client.gpt_api_client import GPTAPIClient
from apis.gpt_client.gpt_response_data import ItemsParser


class RelatedComplianceDataGenerator:

    def __init__(self, cb_client, product, project_id, compliance_tracker_id, downstream_tracker_id, percent):
        self.product = product
        self.project_id = project_id
        self.compliance_tracker_id = compliance_tracker_id
        self.downstream_tracker_id = downstream_tracker_id
        self.percent = percent
        self.cb_client = cb_client

    def generate(self):
        # Initialize gpt client
        gpt_client = GPTAPIClient(1)

        # Get upstream tracker information from id
        upstream_tracker = self.cb_client.tracker_api_instance.get_tracker(self.compliance_tracker_id)
        upstream_tracker_name = upstream_tracker.name
        upstream_tracker_type = upstream_tracker.type.name

        # Get downstream tracker information from id
        downstream_tracker = self.cb_client.tracker_api_instance.get_tracker(self.downstream_tracker_id)
        downstream_tracker_name = downstream_tracker.name
        downstream_tracker_type = downstream_tracker.type.name

        # Gets all items in upstream tracker
        upstream_tracker_items = self.cb_client.get_paginated_tracker_items(
            self.compliance_tracker_id)

        # Calculate the amount of downstream reference items we want
        sample_size = max(1, len(upstream_tracker_items) * self.percent // 100)

        # Create map of upstream items ids and names
        id_name_map = {}
        for tracker_item in random.sample(upstream_tracker_items, sample_size):
            id_name_map[tracker_item.id] = tracker_item.name

        # Get new downstream items from GPT
        response = gpt_client.get_compliance_downstream(id_name_map, self.product, downstream_tracker_name,
                                                        downstream_tracker_type, upstream_tracker_name)
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
    project_id = 6
    upstream_tracker_id = 96427
    downstream_tracker_id = 15303
    percent = 100
    cb_client = CBApiClient()
    cb_client.populate_project_data(project_id)

    # Create an instance of TraceabilityGenerator
    generator = RelatedComplianceDataGenerator(cb_client, "Snowmobile", project_id, upstream_tracker_id,
                                               downstream_tracker_id, percent)

    # Call the generate method
    generator.generate()
