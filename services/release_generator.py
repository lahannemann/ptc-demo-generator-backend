

class ReleaseGenerator:
    def __init__(self, cb_client, tracker_id, item_id_list):
        self.cb_client = cb_client
        self.tracker_id = tracker_id
        self.item_id_list = item_id_list