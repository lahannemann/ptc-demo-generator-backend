import json
import os

import requests


class GPTAPIClient:

    def __init__(self):
        self.azure_api_key = os.getenv("OPENAI_KEY")
        self.azure_endpoint = "https://codebeamerdemogenerator.openai.azure.com/openai/deployments/gpt-4o-mini/chat/completions?api-version=2025-01-01-preview"

    def get_downstream_items(self, id_name_map, product, downstream_tracker_name, upstream_tracker_name,
                             upstream_tracker_type: str, downstream_tracker_type: str, downstream_count: int, additional_rules: str):
        entries = "\n".join(
            [f"- id: {id}, name: {name}" for id, name in id_name_map.items()]
        )
        prompt = f"""
        You are tasked with creating corresponding "{downstream_tracker_name}" {downstream_tracker_type}s to the following "{upstream_tracker_name}" {upstream_tracker_type}s:
        
        {entries}
        
        This data is for the product "{product}" and is intended to support ALM Demo Data.
        
        For each {upstream_tracker_type}, create {downstream_count} corresponding "{downstream_tracker_name}" {downstream_tracker_type} with the following criteria:
        - The new items should have a unique name that is different from the {upstream_tracker_type} name.
        - DO NOT use anything similar to "{downstream_tracker_name}" or any numbers in the new {downstream_tracker_type} names.
        - The new name should be creative and relevant to the {upstream_tracker_type} but distinct.
        - Provide a YAML object for each new {downstream_tracker_type} with:
          - "id": matching the provided id.
          - "name": a unique name for the new {downstream_tracker_type}.
          - "description": a realistically detailed explanation of the {downstream_tracker_type}. This should be formatted to make it look like a real {downstream_tracker_type}
        
        Output example for one entry:
        - id: ...
          name: "..."
          description: "..."
          
        Additional rules: {additional_rules}
    
        Now generate the YAML for all entries. Please don't include any text other than the YAML.
                """
        print("Getting", downstream_tracker_name, "from GPT...")

        yaml_response = self.get_azure_gpt_response(prompt)

        print("Data received from GPT!")

        return yaml_response

    def get_top_level_items(self, product, tracker_name: str, tracker_type: str, item_count: int, requirement_type_prompt_text: str, additional_inputted_rules: str):
        prompt = f"""
            You are tasked with creating {item_count} {tracker_name} {tracker_type}s.
            
            This data is for the product "{product}" and is intended to support ALM Demo Data. {requirement_type_prompt_text} The new items should not be numbered in any way.
            
            Provide a YAML object for each new {tracker_type} with:
            - "name": the name of the new {tracker_type}
            - "description": a realistically detailed explanation of the {tracker_type}. This should be formatted to make it look like a real {tracker_type}
            
            Output example for one entry:
            - name: "..."
              description: "..."
              
            Additional rules: {additional_inputted_rules}
            
            Now generate the YAML for all entries. Please don't include any text other than the YAML.
                """
        print("Getting", tracker_name, "from GPT...")

        yaml_response = self.get_azure_gpt_response(prompt)

        print("Data received from GPT!")

        return yaml_response

    def get_compliance_top_level(self, tracker_name: str, tracker_type: str):
        prompt = f"""
            You are tasked with creating compliance requirements for {tracker_name} .
            
            This data is intended to support ALM Demo Data. It should include all standards within {tracker_name}
            
            Provide a YAML object for each new regulatory {tracker_type} with:
            - "name": the name of the new {tracker_type}
            - "description": a detailed description of the regulatory {tracker_type}
            
            Output example for one entry:
            - name: "..."
              description: "..."
            
            Now generate the YAML for all entries. Please don't include any text other than the YAML.
                """
        print("Getting", tracker_name, "from GPT...")

        yaml_response = self.get_azure_gpt_response(prompt)

        print("Data received from GPT!")

        return yaml_response

    def get_compliance_downstream(self, id_name_map, product, downstream_tracker_name: str, tracker_type: str,
                                  compliance_tracker_name: str):
        entries = "\n".join(
            [f"- id: {id}, name: {name}" for id, name in id_name_map.items()]
        )

        prompt = f"""
            For each of these Regulatory Standard Entries from {compliance_tracker_name}: 
            
            {entries}
            
            You are tasked with creating 2 related {downstream_tracker_name} {tracker_type}s.
            
            This data should be roughly related to a {product} and is intended to support ALM Demo Data. 
            The new {tracker_type}s should not have the same exact name as their parent or include "{downstream_tracker_name}" or the Regulatory Standard Entry name.
                        
            Provide 2 YAML objects for each of the regulatory standard entries. Each YAML object should have the following:
            - "id": matching the provided id.
            - "name": the name of the new {tracker_type} (This should not include the tracker name, tracker type, or upstream standard name, it should just be a brief summary of the {tracker_type})
            - "description": a detailed description of the {tracker_type}
            
            Each parent entry should result in multiple specific requirements that are actionable and detailed. Ensure that the names and descriptions are varied and related to the product.

            It's expected that there will be multiple entries for each item in the list.
                        
            Output example for one entry:
            - id: ...
              name: "..."
              description: "..."
            
            Now generate the YAML for all entries. Please don't include any text other than the YAML.
                """
        print("Getting", downstream_tracker_name, "from GPT...")
        print(prompt)

        yaml_response = self.get_azure_gpt_response(prompt)

        print(yaml_response)

        print("Data received from GPT!")

        return yaml_response

    def get_windchill_parts(self, tracker_item_names, product):

        entries = "\n".join(
            [f"- name: {name}" for name in tracker_item_names]
        )

        prompt = f"""
        You are tasked with creating corresponding PLM Windchill Parts for the following requirements:
        
        {entries}
        
        This data is for the product "{product}" and is intended to support ALM Demo Data.
        
        For each requirement, create a corresponding Windchill Part with the following criteria:
        - The new items should have a unique name that is different from the requirement name.
        - The parts should be realistic and detailed
        - Provide a YAML object for each new Windchill Part with:
          - "id": abbreviated version of the name - ideally at least 5 letters
          - "part_name": a name for the new Windchill Part with spaces
          - "requirement_name": the requirement it corresponds to
        
        Output example for one entry:
        - id: ...
          part_name: "..."
          requirement_name: "..."
              
    Now generate the YAML for all entries. Please don't include any text other than the YAML.
                """
        print("Getting Windchill Parts from GPT...")

        yaml_response = self.get_azure_gpt_response(prompt)

        print(yaml_response)

        print("Data received from GPT!")

        return yaml_response

    def get_test_steps(self, product, test_case_name):
        prompt = f"""
            You are tasked with creating 2 test steps for a test case called {test_case_name}. 
            This is to support an ALM demo for a {product}.
            
            Provide a YAML object for each test step with:
            - "action": The action the tester should take for this test
            - "expected_result": The expected result for this action
            
            Output example for one entry:
            - action: "..."
              expected_result: "..."
              
            Now generate the YAML. Please don't include any text other than the YAML.
        """

        print("Getting test steps from GPT...")

        yaml_response = self.get_azure_gpt_response(prompt)

        print("Data received from GPT!")

        return yaml_response

    def get_azure_gpt_response(self, prompt):
        # Request headers
        headers = {
            "Content-Type": "application/json",
            "api-key": self.azure_api_key
        }

        # Request body
        data = {
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 4000,
            "temperature": 0.5
        }

        # Make the POST request
        response = requests.post(self.azure_endpoint, headers=headers, data=json.dumps(data))

        # Check response
        if response.status_code == 200:
            result = response.json()
        else:
            print(f"Error: {response.status_code}, {response.text}")

        yaml_response = result["choices"][0]["message"]["content"]

        # Remove any leading/trailing whitespace or newlines
        yaml_response_cleaned = yaml_response.strip()

        # Remove the leading "```yaml" or similar markers
        if yaml_response_cleaned.startswith("```yaml"):
            yaml_response_cleaned = yaml_response_cleaned[7:]  # Remove the first 7 characters ("```yaml")

        # Remove trailing "```" or any similar backticks
        if yaml_response_cleaned.endswith("```"):
            yaml_response_cleaned = yaml_response_cleaned[:-3]  # Remove the last 3 characters ("```")

        # Strip any remaining backticks or whitespace
        yaml_response_cleaned = yaml_response_cleaned.strip('`').strip()

        return yaml_response_cleaned
