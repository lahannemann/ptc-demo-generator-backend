from concurrent.futures import ThreadPoolExecutor


class DeleteAllTrackerData:
    def __init__(self, cb_client, tracker_id):
        self.cb_client = cb_client
        self.tracker_id = tracker_id

    def generate(self):
        while True:
            all_tracker_items_response = self.cb_client.tracker_api_instance.get_items_by_tracker(self.tracker_id, 1, 500)
            item_count = len(all_tracker_items_response.item_refs)
            print("Found " + str(item_count) + " items in " + str(self.tracker_id))

            if item_count == 0:
                break

            with ThreadPoolExecutor() as executor:
                futures = [executor.submit(self.delete_tracker_item, item) for item in all_tracker_items_response.item_refs]
                for future in futures:
                    future.result()  # Wait for all futures to complete

    def delete_tracker_item(self, item):
        self.cb_client.tracker_item_api_instance.delete_tracker_item(item.id)
        print("Deleting " + str(item.name))


if __name__ == "__main__":
    # Input data
    tracker_id = 55

    # Create an instance of DeleteAllProjectData
    generator = DeleteAllTrackerData(tracker_id)

    # Call the generate method
    generator.generate()
