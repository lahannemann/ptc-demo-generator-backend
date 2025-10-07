import requests
from requests.auth import HTTPBasicAuth


def main():
    # Credentials and URLs
    username = ""
    password = ""
    base_url = "https://pp-25072118407s.portal.ptc.io/Windchill/servlet/odata"
    parts_url = f"{base_url}/ProdMgmt/Parts"
    csrf_url = f"{base_url}/PTC/GetCSRFToken"

    # Start a session
    session = requests.Session()
    session.auth = HTTPBasicAuth(username, password)

    # Trigger session and get cookies
    session.get(base_url)

    # Get CSRF token
    csrf_response = session.get(csrf_url)
    if csrf_response.status_code != 200:
        print("Failed to retrieve CSRF token.")
        print(csrf_response.text)
        return

    csrf_data = csrf_response.json()
    nonce_key = csrf_data.get("NonceKey")
    nonce_value = csrf_data.get("NonceValue")

    if not nonce_key or not nonce_value:
        print("CSRF token missing in response.")
        print(csrf_data)
        return

    # Prepare headers with CSRF token
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        nonce_key: nonce_value
    }

    # Step 4: Define payload
    payload = {
        "Name": "TestWTPart_001",
        "Number": "TP001",
        "AssemblyMode": {
            "Value": "separable",
            "Display": "Separable"
        },
        "PhantomManufacturingPart": False,
        "Context@odata.bind": "Containers('OR:wt.pdmlink.PDMLinkProduct:8509940')",
        "EndItem": True,
        "DefaultUnit": {
            "Value": "ea"
        },
        "DefaultTraceCode": {
            "Value": "0",
            "Display": "Untraced"
        },
        "Source": {
            "Value": "make",
            "Display": "Make"
        },
        "GatheringPart": False,
        "ConfigurableModule": {
            "Value": "standard",
            "Display": "No"
        }
    }

    # Make POST request to create part
    response = session.post(parts_url, json=payload, headers=headers)

    if response.status_code == 201:
        print("Part created successfully!")
        print(response.json())
    else:
        print(f"Failed to create part: {response.status_code}")
        print(response.text)


if __name__ == "__main__":
    main()
