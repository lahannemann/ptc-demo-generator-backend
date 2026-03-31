from openapi_client import UpdateTrackerItemField

from apis.cb_client.cb_api_client import CBApiClient
from apis.cb_client.utils import Utils
from apis.gpt_client.gpt_api_client import GPTAPIClient
from apis.gpt_client.gpt_response_data import ItemsParser


class DownstreamTraceabilityGenerator:

    def __init__(self, cb_client, product, upstream_tracker_id, upstream_items, downstream_tracker_id, downstream_field_id, downstream_count, additional_rules):
        self.product = product
        self.upstream_tracker_id = upstream_tracker_id
        self.upstream_items = upstream_items
        self.downstream_tracker_id = downstream_tracker_id
        self.downstream_field_id = downstream_field_id
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

        # Get downstream tracker information from id
        downstream_tracker = self.cb_client.tracker_api_instance.get_tracker(self.downstream_tracker_id)
        downstream_tracker_name = downstream_tracker.name
        downstream_tracker_type = downstream_tracker.type.name

        # Create map of upstream items ids and names
        id_name_map = {item['id']: item['name'] for item in self.upstream_items}

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
            # upstream_reference = Utils.get_abstract_reference_tracker_item(item.parent_id)

            new_added_item = self.cb_client.create_generic_tracker_item(
               self.downstream_tracker_id, item.name, item.description, None)

            update_field_item = UpdateTrackerItemField()
            update_field_item.field_values = []
            tracker_item_fields = self.cb_client.tracker_item_api_instance.get_tracker_item_fields(new_added_item.id)

            for field in tracker_item_fields.editable_fields:
                if field.field_id == self.downstream_field_id:
                    setattr(field, "values", [Utils.get_abstract_reference_tracker_item(item.parent_id)])
                    update_field_item.field_values.append(field)

            self.cb_client.tracker_item_api_instance.update_custom_field_tracker_item(new_added_item.id, update_field_item)


if __name__ == "__main__":
    # Input data
    product = "Racecar"
    upstream_tracker_id = 109023
    downstream_tracker_id = 109020
    downstream_field_id = 1002
    cb_client = CBApiClient("https://pp-2602121357rr.portal.ptc.io:9443/cb", "pat", "ptc")
    # cb_client.populate_project_data(project_id)
    tracker_items = [
        {"id": item.id, "name": item.name}
        for item in cb_client.get_paginated_tracker_items(int(upstream_tracker_id))
    ]

    # Create an instance of TraceabilityGenerator
    generator = DownstreamTraceabilityGenerator(cb_client, product, upstream_tracker_id, tracker_items, downstream_tracker_id, downstream_field_id, 1, "")

    # Call the generate method
    generator.generate()
