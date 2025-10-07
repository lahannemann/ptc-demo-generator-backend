from concurrent.futures import ThreadPoolExecutor


class DeleteAllProjectData:
    def __init__(self, cb_api_client, project_id):
        self.cb_api_client = cb_api_client
        self.project_id = project_id

    def generate(self):
        all_trackers = self.cb_api_client.project_api_instance.get_trackers(self.project_id)
        items_found = True
        while items_found:
            items_found = False
            for tracker in all_trackers:
                if self.delete_all_tracker_data(tracker.id):
                    items_found = True

    def delete_all_tracker_data(self, tracker_id):
        items_found = False
        all_tracker_items_response = self.cb_api_client.tracker_api_instance.get_items_by_tracker(
            tracker_id, 1, 500)
        if len(all_tracker_items_response.item_refs) > 0:
            items_found = True
        print("Found " + str(len(all_tracker_items_response.item_refs)) + " items in " + str(tracker_id))

        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(self.delete_tracker_item, item) for item in all_tracker_items_response.item_refs]
            for future in futures:
                future.result()  # Wait for all futures to complete
        return items_found

    def delete_tracker_item(self, item):
        self.cb_api_client.tracker_item_api_instance.delete_tracker_item(item.id)
        print("Deleting " + str(item.name))


if __name__ == "__main__":
    # Input data
    project_id = 55

    # Create an instance of DeleteAllProjectData
    generator = DeleteAllProjectData(project_id)

    # Call the generate method
    generator.generate()
