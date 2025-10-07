import requests
from requests.auth import HTTPBasicAuth

from apis.cb_client.cb_api_client import CBApiClient


class TestWindchill:
    def __init__(self, username, password, base_url):
        self.base_url = base_url
        self.parts_url = f"{base_url}/ProdMgmt/Parts"
        self.products_url = f"{base_url}/DataAdmin/Containers/PTC.DataAdmin.ProductContainer"
        self.csrf_url = f"{base_url}/PTC/GetCSRFToken"
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(username, password)

        # Trigger session and get cookies
        self.session.get(base_url)

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

    def create_part(self, name, number, context_bind):
        payload = {
            "Name": name,
            "Number": number,
            "AssemblyMode": {"Value": "separable", "Display": "Separable"},
            "PhantomManufacturingPart": False,
            "Context@odata.bind": context_bind,
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



if __name__ == "__main__":
    # Initialize client
    client = TestWindchill(
        username="",
        password="",
        base_url="https://pp-25072118407s.portal.ptc.io/Windchill/servlet/odata"
    )

    # Example: Create a part
    name = "TestWTPart_006"
    number = "TP006"
    context_bind = "Containers('OR:wt.pdmlink.PDMLinkProduct:8509940')"

    # created_part = client.create_part(name, number, context_bind)
    # if created_part:
    #     print("Created Part Info:")
    #     print(created_part)

    cb_api_client = CBApiClient("https://pp-2506061501b4.portal.ptc.io:9443/cb", "", "")
    all_items = cb_api_client.get_paginated_tracker_items(50782)
    tracker_item_map = {item.name: item.id for item in all_items}
    print(tracker_item_map)
    # print("FOUND: " + tracker_item_map[name])

    # Example: Get product container details
    # Example: Get product name-to-ID map
    product_map = client.get_products()
    print("\nProduct Name → ID Map:")
    for name, product_id in product_map.items():
        print(f"{name} → {product_id}")

