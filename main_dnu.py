
import anvil.server
from openapi_client.exceptions import ServiceException, UnauthorizedException, NotFoundException

from apis.cb_client.cb_api_client import CBApiClient
from apis.windchill_client.windchill_api_client import WindchillApiClient
from services.batch_item_generation import BatchItemGeneration
from services.delete_all_project_data import DeleteAllProjectData
from services.delete_all_tracker_data import DeleteAllTrackerData
from services.field_updater import FieldUpdater
from services.status_updater import StatusUpdater
from services.test_run_generator import TestRunGenerator
from services.test_step_generator import TestStepGenerator
from services.top_level_item_generator import TopLevelItemGenerator
from services.traceability_generator import TraceabilityGenerator

import builtins
import anvil.server
import os

import traceback
import functools

from session_logger import SessionLogger


# Wrapper so any exception thrown in a method tagged with this @log_exceptions is printed
def log_exceptions(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"Exception in {func.__name__}: {e}")
            traceback.print_exc()
            raise
    return wrapper


class Main:

    def __init__(self):
        self.session_store = {}

        # This is how we connect to anvil. This starts a listener for requests from anvil to this key
        anvil.server.connect(os.getenv("ANVIL_UPLINK_KEY"))
        self.logger = SessionLogger(self.session_store)

        # Don't think this is being used but need to check before deleting
        @anvil.server.callable
        @log_exceptions
        def store_session_id(session_id):
            self.session_id = session_id

        # Ping from client to make sure server is running so error can be displayed if not
        @anvil.server.callable
        @log_exceptions
        def ping():
            return "pong"

        # Checks to make sure user is connected to a Codebeamer server before attempting tasks
        @anvil.server.callable
        @log_exceptions
        def check_for_connection():
            session_id = anvil.server.get_session_id()
            if session_id not in self.session_store or self.session_store[session_id].get("cb_api_client") is None:
                raise Exception("Codebeamer server not connected. Please connect to a server before proceeding.")

        # Called when user connects to Codebeamer, stores Codebeamer client on session,
        # gets all cb projects and stores those on session as well
        @anvil.server.callable
        @log_exceptions
        def load_codebeamer_server(url, username, password, user_email):
            session_id = anvil.server.get_session_id()
            if session_id not in self.session_store:
                self.session_store[session_id] = {}
            self.session_store[session_id]["user_email"] = user_email
            self.logger.info("Connecting to Codebeamer server...")
            cb_api_client = CBApiClient(url, username, password)
            self.session_store[session_id]["cb_url"] = url
            self.session_store[session_id]["cb_api_client"] = cb_api_client

            try:
                self.logger.info("Getting all projects...")
                projects = cb_api_client.project_api_instance.get_projects()
            except ServiceException:
                self.session_store[session_id]["cb_api_client"] = None
                raise Exception("Server Error: Please confirm server is running")
            except UnauthorizedException:
                self.session_store[session_id]["cb_api_client"] = None
                raise Exception("Unauthorized: Please check your username and password")
            except NotFoundException:
                self.session_store[session_id]["cb_api_client"] = None
                raise Exception(
                    "The server was not found. Please ensure your URL is pointing to a Codebeamer instance.")
            except Exception as e:
                self.logger.info(str(e))
                raise

            project_map = {project.name: project.id for project in projects}
            self.session_store[session_id]["project_map"] = project_map
            self.logger.info("Connected to Codebeamer server")
            return list(project_map.keys())

        # Clears all codebeamer server related data from the session when user disconnects from server
        @anvil.server.callable
        @log_exceptions
        def disconnect_codebeamer_server():
            self.logger.info("Disconnecting from Codebeamer server...")
            session_id = anvil.server.get_session_id()
            if "cb_api_client" in self.session_store[session_id]:
                del self.session_store[session_id]["cb_api_client"]
            if "project_id" in self.session_store[session_id]:
                del self.session_store[session_id]["project_id"]
            if "project_map" in self.session_store[session_id]:
                del self.session_store[session_id]["project_map"]
            if "product" in self.session_store[session_id]:
                del self.session_store[session_id]["product"]
            if "cb_url" in self.session_store[session_id]:
                del self.session_store[session_id]["cb_url"]
            self.logger.info("Disconnected to Codebeamer server")

        # Stores selected Project on session
        @anvil.server.callable
        @log_exceptions
        def populate_project_data(project_name):
            self.logger.info("Storing project data...")
            session_id = anvil.server.get_session_id()
            project_map = self.session_store.get(session_id).get("project_map")
            project_id = project_map[project_name]
            self.session_store[session_id]["project_id"] = project_id
            cb_api_client = self.session_store.get(session_id).get("cb_api_client")
            cb_api_client.populate_project_data(project_id)
            self.logger.info("Project data stored")
            return list(cb_api_client.get_tracker_map().keys())

        # Gets selected project id from session
        @anvil.server.callable
        @log_exceptions
        def get_project_id():
            session = self.session_store.get(anvil.server.get_session_id())
            if session:
                return session.get("project_id")
            else:
                return None

        # Gets codebeamer server url from session (Used to populate url field when returning to setup page)
        @anvil.server.callable
        @log_exceptions
        def get_connected_server_url():
            session = self.session_store.get(anvil.server.get_session_id())
            if session:
                return session.get("cb_url")
            else:
                return None

        # Gets list of projects for connected codebeamer server from session
        @anvil.server.callable
        @log_exceptions
        def get_project_list():
            session = self.session_store.get(anvil.server.get_session_id())
            return list(session.get("project_map").keys())

        # Gets the product stored on session
        @anvil.server.callable
        @log_exceptions
        def get_product():
            session = self.session_store.get(anvil.server.get_session_id())
            return session.get("product")

        # Gets list of trackers for the selected project (This is set on client when project is selected)
        @anvil.server.callable
        @log_exceptions
        def get_tracker_list():
            session = self.session_store.get(anvil.server.get_session_id())
            return list(session.get("cb_api_client").get_tracker_map().keys())

        # Sets product on session
        @anvil.server.callable
        @log_exceptions
        def set_product(product):
            self.logger.info("Setting product (" + product + ")...")
            session_id = anvil.server.get_session_id()
            self.session_store[session_id]["product"] = product
            self.logger.info("Product set")

        # Gets the name of the project stored on session
        @anvil.server.callable
        @log_exceptions
        def get_project_name():
            session = self.session_store.get(anvil.server.get_session_id())
            for name, id_value in session.get("project_map").items():
                if id_value == session.get("project_id"):
                    return name
            return None

        # Generate top level items
        @anvil.server.callable
        @log_exceptions
        def generate_top_level_items(requirement_type, tracker_name, item_count, additional_rules):
            self.logger.info("Generating top level items...")
            session = self.session_store.get(anvil.server.get_session_id())
            tracker_id = session.get("cb_api_client").get_tracker_id(tracker_name)
            TopLevelItemGenerator(session.get("cb_api_client"), session.get("product"), session.get("project_id"),
                                  tracker_id, item_count, requirement_type, additional_rules).generate()
            self.logger.info("Generated top level items")

        # Delete all project data
        @anvil.server.callable
        @log_exceptions
        def delete_all_project_data():
            self.logger.info("Deleting all project data...")
            session = self.session_store.get(anvil.server.get_session_id())
            DeleteAllProjectData(session.get("cb_api_client"), session.get("project_id")).generate()
            self.logger.info("Deleted all project data")

        # Delete all tracker data
        @anvil.server.callable
        @log_exceptions
        def delete_all_tracker_data(tracker_name):
            self.logger.info("Deleting all tracker data (" + tracker_name + ")...")
            session = self.session_store.get(anvil.server.get_session_id())
            tracker_id = session.get("cb_api_client").get_tracker_id(tracker_name)
            DeleteAllTrackerData(session.get("cb_api_client"), tracker_id).generate()
            self.logger.info("Deleted all tracker data")

        # Get names of the tracker items for given tracker
        @anvil.server.callable
        @log_exceptions
        def get_tracker_items(tracker_name):
            session = self.session_store.get(anvil.server.get_session_id())
            tracker_id = session.get("cb_api_client").get_tracker_id(tracker_name)
            tracker_items = session.get("cb_api_client").get_paginated_tracker_items(tracker_id)
            tracker_item_map = {item.name: item.id for item in tracker_items}
            return list(tracker_item_map.keys())[::-1]

        # Generate downstream traceability
        @anvil.server.callable
        @log_exceptions
        def generate_traceability(upstream_tracker_name, select_all, upstream_items, downstream_tracker_name,
                                  item_count_per_upstream, additional_rules):
            self.logger.info("Generating traceability...")
            session = self.session_store.get(anvil.server.get_session_id())
            cb_api_client = session.get("cb_api_client")
            upstream_tracker_id = cb_api_client.get_tracker_id(upstream_tracker_name)
            downstream_tracker_id = cb_api_client.get_tracker_id(downstream_tracker_name)
            tracker_items = cb_api_client.get_paginated_tracker_items(upstream_tracker_id)
            tracker_item_map = {item.name: item.id for item in tracker_items}
            if not select_all:
                tracker_item_map = {key: tracker_item_map[key] for key in upstream_items if key in tracker_item_map}

            TraceabilityGenerator(cb_api_client, session.get("product"), session.get("project_id"), upstream_tracker_id,
                                  tracker_item_map, downstream_tracker_id, item_count_per_upstream,
                                  additional_rules).generate()
            self.logger.info("Generated traceability")

        # Update item statuses
        @anvil.server.callable
        @log_exceptions
        def update_statuses(tracker_name, select_all, tracker_items):
            self.logger.info("Updating item statuses...")
            session = self.session_store.get(anvil.server.get_session_id())
            cb_api_client = session.get("cb_api_client")
            tracker_id = cb_api_client.get_tracker_id(tracker_name)
            all_tracker_items = cb_api_client.get_paginated_tracker_items(tracker_id)
            tracker_item_map = {item.name: item.id for item in all_tracker_items}
            if not select_all:
                tracker_item_map = {key: tracker_item_map[key] for key in tracker_items if key in tracker_item_map}

            StatusUpdater(cb_api_client, tracker_id, tracker_item_map.values()).generate()
            self.logger.info("Updated item statuses")

        # Update item metadata
        @anvil.server.callable
        @log_exceptions
        def update_metadata(tracker_name, select_all, tracker_items):
            self.logger.info("Updating item metadata...")
            session = self.session_store.get(anvil.server.get_session_id())
            cb_api_client = session.get("cb_api_client")
            tracker_id = cb_api_client.get_tracker_id(tracker_name)
            all_tracker_items = cb_api_client.get_paginated_tracker_items(tracker_id)
            tracker_item_map = {item.name: item.id for item in all_tracker_items}
            if not select_all:
                tracker_item_map = {key: tracker_item_map[key] for key in tracker_items if key in tracker_item_map}

            FieldUpdater(cb_api_client, tracker_id, tracker_item_map.values()).generate()
            self.logger.info("Updated item metadata")

        # Generate test run data
        @anvil.server.callable
        @log_exceptions
        def generate_test_run(test_case_tracker_name, select_all, selected_tracker_items, test_run_tracker_name,
                              passed_count, failed_count, blocked_count):
            self.logger.info("Generating test run...")
            session = self.session_store.get(anvil.server.get_session_id())
            cb_api_client = session.get("cb_api_client")
            test_case_tracker_id = cb_api_client.get_tracker_id(test_case_tracker_name)
            test_run_tracker_id = cb_api_client.get_tracker_id(test_run_tracker_name)
            all_test_cases = cb_api_client.get_paginated_tracker_items(test_case_tracker_id)
            if not select_all:
                all_test_cases = [test_case for test_case in all_test_cases if test_case.name in selected_tracker_items]

            TestRunGenerator(cb_api_client, test_case_tracker_id, all_test_cases, test_run_tracker_id, passed_count,
                             failed_count, blocked_count).generate()
            self.logger.info("Generated test run")

        # Generate test steps
        @anvil.server.callable
        @log_exceptions
        def generate_test_steps(test_case_tracker_name, selected_items):
            self.logger.info("Generating test steps...")
            session = self.session_store.get(anvil.server.get_session_id())
            cb_api_client = session.get("cb_api_client")
            test_case_tracker_id = cb_api_client.get_tracker_id(test_case_tracker_name)
            all_tracker_items = cb_api_client.get_paginated_tracker_items(test_case_tracker_id)
            tracker_item_map = {item.name: item.id for item in all_tracker_items}
            tracker_item_map = {key: tracker_item_map[key] for key in selected_items if key in tracker_item_map}

            TestStepGenerator(cb_api_client, session.get("product"), test_case_tracker_id,
                              tracker_item_map.values()).generate()
            self.logger.info("Generated test steps")

        # Generate batch items
        @anvil.server.callable
        @log_exceptions
        def generate_batch_items(tracker_name, count):
            self.logger.info("Generating batch items...")
            session = self.session_store.get(anvil.server.get_session_id())
            cb_api_client = session.get("cb_api_client")
            tracker_id = cb_api_client.get_tracker_id(tracker_name)

            BatchItemGeneration(cb_api_client, tracker_id, tracker_name, count).generate()
            self.logger.info("Generated batch items")

        # WINDCHILL
        @anvil.server.callable
        @log_exceptions
        def connect_windchill_server(url, username, password):
            session_id = anvil.server.get_session_id()
            windchill_api_client = WindchillApiClient(url, username, password)
            self.session_store[session_id]["windchill_api_client"] = windchill_api_client

        @anvil.server.callable
        @log_exceptions
        def get_windchill_products():
            session_id = anvil.server.get_session_id()
            session = self.session_store.get(session_id)
            windchill_api_client = session.get("windchill_api_client")
            windchill_product_map = windchill_api_client.get_products()
            print(windchill_product_map)
            self.session_store[session_id]["wc_product_map"] = windchill_product_map
            return list(windchill_product_map.keys())[::-1]

        @anvil.server.callable
        @log_exceptions
        def generate_windchill_parts(tracker_name, product_name):
            session_id = anvil.server.get_session_id()
            session = self.session_store.get(session_id)
            windchill_api_client = session.get("windchill_api_client")
            windchill_product_map = session.get("wc_product_map")
            cb_api_client = session.get("cb_api_client")
            tracker_id = cb_api_client.get_tracker_id(tracker_name)
            all_tracker_items = cb_api_client.get_paginated_tracker_items(tracker_id)
            windchill_api_client.generate_parts_list(all_tracker_items, session.get("product"), windchill_product_map[product_name])

        # This is what keeps the connection open - very important!
        anvil.server.wait_forever()


main_instance = Main()
