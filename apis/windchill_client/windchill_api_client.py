import requests
from requests.auth import HTTPBasicAuth

from apis.gpt_client.gpt_api_client import GPTAPIClient
from apis.gpt_client.gpt_response_data import WindchillPartParser


class WindchillApiClient:

    def __init__(self, url, username, password):
        self.base_url = url + "/servlet/odata"
        self.parts_url = f"{self.base_url}/ProdMgmt/Parts"
        self.products_url = f"{self.base_url}/DataAdmin/Containers/PTC.DataAdmin.ProductContainer"
        self.csrf_url = f"{self.base_url}/PTC/GetCSRFToken"
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(username, password)

        # Trigger session and get cookies
        self.session.get(self.base_url)

        # Get CSRF token
        csrf_response = self.session.get(self.csrf_url)
        if csrf_response.status_code != 200:
            raise Exception("Failed to retrieve CSRF token.")

        csrf_data = csrf_response.json()
        self.nonce_key = csrf_data.get("NonceKey")
        self.nonce_value = csrf_data.get("NonceValue")

        if not self.nonce_key or not self.nonce_value:
            raise Exception("CSRF token missing in response.")

        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            self.nonce_key: self.nonce_value
        }

    def get_products(self):
        response = self.session.get(self.products_url, headers=self.headers)
        if response.status_code == 200:
            data = response.json()
            products = data.get("value", [])
            return {product["Name"]: product["ID"] for product in products}
        else:
            print(f"❌ Failed to retrieve product containers: {response.status_code}")
            print(response.text)
            return {}

    def generate_parts_list(self, tracker_items, product, context_bind):
        gpt_client = GPTAPIClient()
        tracker_item_names = [item.name for item in tracker_items]
        parts = gpt_client.get_windchill_parts(tracker_item_names, product)

        parser = WindchillPartParser(parts)
        new_parts = parser.get_items()

        for part in new_parts:
            self.create_part(part.part_name, part.part_id, context_bind)

    def create_part(self, name, number, context_bind):
        payload = {
            "Name": name,
            "Number": number,
            "AssemblyMode": {"Value": "separable", "Display": "Separable"},
            "PhantomManufacturingPart": False,
            "Context@odata.bind": "Containers('" + context_bind + "')",
            "EndItem": True,
            "DefaultUnit": {"Value": "ea"},
            "DefaultTraceCode": {"Value": "0", "Display": "Untraced"},
            "Source": {"Value": "make", "Display": "Make"},
            "GatheringPart": False,
            "ConfigurableModule": {"Value": "standard", "Display": "No"}
        }

        response = self.session.post(self.parts_url, json=payload, headers=self.headers)
        if response.status_code == 201:
            print("✅ Part created successfully!")
            return response.json()
        else:
            print(f"❌ Failed to create part: {response.status_code}")
            print(response.text)
            return None
