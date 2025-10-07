import concurrent.futures

from openapi_client import TrackerItem


class BatchItemGeneration:
    def __init__(self, cb_client, tracker_id, tracker_name, count):
        self.cb_client = cb_client
        self.tracker_id = tracker_id
        self.tracker_name = tracker_name
        self.count = count

    def generate(self):
        print("Generating batch items...")
        # Use ThreadPoolExecutor for parallelism
        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.map(self.create_tracker_item, range(1, self.count))

    def create_tracker_item(self, i):
        tracker_item = TrackerItem()
        tracker_item.name = self.tracker_name + " " + str(i)
        tracker_item.description = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."

        self.cb_client.tracker_item_api_instance.create_tracker_item(
            self.tracker_id, tracker_item)
        print("Added " + tracker_item.name)
