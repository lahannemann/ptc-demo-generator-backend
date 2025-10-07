import random

from openapi_client import OptionChoiceField, UpdateTrackerItemField, UserChoiceField, TrackerItemChoiceField

from apis.cb_client.cb_api_client import CBApiClient
from apis.cb_client.utils import Utils


# This class updates fields on tracker items to random values
class FieldUpdater:
    _fields_to_ignore = {"ID", "Summary", "Tracker", "Submitted at", "Submitted by", "Parent", "Children",
                         "Description", "Description Format", "Attachments", "Status"}

    def __init__(self, cb_client: CBApiClient, tracker_id, item_id_list):
        self.cb_client = cb_client
        self.tracker_id = tracker_id
        self.item_id_list = item_id_list

    def generate(self):
        print("Updating metadata...")

        for item_id in self.item_id_list:
            update_field_item = UpdateTrackerItemField()
            update_field_item.field_values = []
            tracker_item_fields = self.cb_client.tracker_item_api_instance.get_tracker_item_fields(item_id)

            for field in tracker_item_fields.editable_fields:
                if field.type == "ChoiceFieldValue" and not self._fields_to_ignore.__contains__(field.name):
                    detailed_field = self.cb_client.tracker_api_instance.get_tracker_field(self.tracker_id, field.field_id)
                    if isinstance(detailed_field, OptionChoiceField):
                        # TODO: Add code to make sure we arent changing the type of folder/information items
                        valid_options = Utils.get_valid_ids(detailed_field.options)
                        if valid_options:
                            new_choice_id = Utils.get_random_option_from_list(valid_options)
                            setattr(field, "values", [new_choice_id])
                            update_field_item.field_values.append(field)
                    elif isinstance(detailed_field, UserChoiceField):
                        user = Utils.get_abstract_reference_user(random.choice(self.cb_client.member_ids))
                        setattr(field, "values", user)
                        update_field_item.field_values.append(field)
                elif field.type == "IntegerFieldValue" and not self._fields_to_ignore.__contains__(field.name):
                    setattr(field, "value", random.randint(1, 10))
                    update_field_item.field_values.append(field)

            self.cb_client.tracker_item_api_instance.update_custom_field_tracker_item(item_id, update_field_item)


if __name__ == "__main__":
    # Input data
    project_id = 24
    tracker_id = 68981
    cb_api_client = CBApiClient("https://pp-25031818218l.portal.ptc.io:9443/cb", "pat", "ptc")
    cb_api_client.populate_project_data(project_id)

    # Create an instance of DeleteAllProjectData
    generator = FieldUpdater(cb_api_client, tracker_id, [12164])

    # Call the generate method
    generator.generate()


