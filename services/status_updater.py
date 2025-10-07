import random
from collections import defaultdict

from apis.cb_client.utils import Utils


class StatusUpdater:
    def __init__(self, cb_client, tracker_id, item_id_list):
        self.cb_client = cb_client
        self.tracker_id = tracker_id
        self.item_id_list = item_id_list
        self.transition_map = defaultdict(set)

    def generate(self):
        print("Updating statuses...")
        # Gets all the possible transitions from the current item status (new)
        possible_transitions = self.cb_client.tracker_api_instance.get_tracker_transitions(self.tracker_id)
        for transition in possible_transitions:
            from_id = transition.from_status.id
            to_id = transition.to_status.id

            if transition.to_status.name != "Rejected":
                self.transition_map[from_id].add(to_id)
                self.transition_map[from_id].add(from_id)

        # Moves each item to a random status that's valid from it's current status
        for item_id in self.item_id_list:
            tracker_item = self.cb_client.tracker_item_api_instance.get_tracker_item(item_id)
            current_status = tracker_item.status.id
            next_transition = self.transition_map.get(current_status, set())
            next_transition = list(next_transition)

            tracker_item.status = Utils.get_abstract_reference_choice(random.choice(next_transition))
            try:
                self.cb_client.tracker_item_api_instance.update_tracker_item(item_id, tracker_item)
            except Exception as e:
                print(e)
