import random

from openapi_client import ApiClient, Configuration, TrackerItemApi, TrackerApi, TestRunApi, ProjectApi

from apis.cb_client.utils import Utils


class CBApiClient:
    _member_ids = []

    def __init__(self, url, username, password):
        config = Configuration()
        config.username = username
        config.password = password
        config.host = url + "/api"
        api_client = ApiClient(configuration=config)

        self.tracker_api_instance = TrackerApi(api_client)
        self.tracker_item_api_instance = TrackerItemApi(api_client)
        self.test_run_api_instance = TestRunApi(api_client)
        self.project_api_instance = ProjectApi(api_client)

    # Populates project relevant data
    def populate_project_data(self, project_id):
        self._member_ids = []
        self.populate_member_ids(project_id)

    # Creates tracker item
    def create_generic_tracker_item(self, tracker_id: int, name: str, description: str, upstream):
        new_tracker_item = Utils.create_tracker_item_object(name)
        new_tracker_item.description = description
        if upstream is not None:
            new_tracker_item.subjects = [upstream]

        print("Adding " + name + " to " + str(tracker_id) + " tracker...")

        response_object = self.tracker_item_api_instance.create_tracker_item(
            tracker_id, new_tracker_item)
        return response_object

    # Creates list of all members on project
    def populate_member_ids(self, project_id):
        members = self.project_api_instance.get_members_of_project(project_id)
        user_references = members.members  # contains the list of UserReference objects

        # Collect member IDs
        for user_ref in user_references:
            self._member_ids.append(user_ref.id)  # Collect the ID

    def get_paginated_tracker_items(self, tracker_id):
        page_size = 100
        sample = self.tracker_api_instance.get_items_by_tracker(tracker_id, 1, page_size)
        total_items = sample.total
        page_count = (total_items + page_size - 1) // page_size

        all_items = []

        for page in range(1, page_count + 1):
            items = self.tracker_api_instance.get_items_by_tracker(tracker_id, page, page_size).item_refs
            all_items.extend(items)

        return all_items

    @property
    def member_ids(self):
        return self._member_ids
