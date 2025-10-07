import random

from openapi_client import AbstractReference, TrackerItem, TrackerItemReference


class Utils:

    @staticmethod
    def get_abstract_reference_choice(item_id: int):
        abstract_reference = AbstractReference()
        abstract_reference.id = item_id
        abstract_reference.type = "ChoiceOptionReference"

        return abstract_reference

    @staticmethod
    def get_abstract_reference_user(item_id: int):
        abstract_reference = AbstractReference(id=item_id, name=None, type="UserReference")
        return [abstract_reference]

    @staticmethod
    def get_abstract_reference_tracker_item(item_id: int):
        abstract_reference = AbstractReference(id=item_id, name=None, type="TrackerItemReference")
        return abstract_reference

    @staticmethod
    def create_tracker_item_object(name: str):
        tracker_item = TrackerItem()
        tracker_item.name = name

        return tracker_item

    @staticmethod
    def create_tracker_item_reference_object(id: int):
        tracker_item_reference = TrackerItemReference()
        tracker_item_reference.id = id
        tracker_item_reference.type = "TrackerItemReference"

        return tracker_item_reference

    @staticmethod
    def get_random_option_from_list(valid_ids):
        return Utils.get_abstract_reference_choice(random.choice(valid_ids))

    @staticmethod
    def get_valid_ids(options):
        valid_ids = []
        for option in options:
            if option.name != "Information" and option.name != "Folder" and option.name != "Unset" and option.name != "Theme":
                valid_ids.append(option.id)
        return valid_ids
