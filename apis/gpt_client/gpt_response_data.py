from typing import List

import yaml


class GenericItem:
    def __init__(self, name: str, description: str, parent_id: int):
        self.name = name
        self.description = description
        self.parent_id = parent_id


class TestStep:
    def __init__(self, action: str, expected_result: str):
        self.action = action
        self.expected_result = expected_result


class WindchillPart:
    def __init__(self, part_id: str, part_name: str, requirement_name: str):
        self.part_id = part_id
        self.part_name = part_name
        self.requirement_name = requirement_name


class ItemsParser:
    def __init__(self, yaml_data: str):
        self.yaml_data = yaml_data
        self.items: List[GenericItem] = []
        self._parse_yaml()

    def _parse_yaml(self):
        # Parse the YAML string
        data = yaml.safe_load(self.yaml_data)

        # Check if the parsed data is a list
        if not isinstance(data, list):
            raise ValueError("Invalid YAML format. Expected a top-level list.")

        for item in data:
            # Ensure each item has the required keys
            if not all(key in item for key in ["name", "description"]):
                raise ValueError(f"Missing keys in item: {item}")

            # Create and append new item
            self.items.append(
                GenericItem(item["name"], item["description"], item.get("id"))
            )

    def get_items(self) -> List[GenericItem]:
        return self.items


class TestStepParser:
    def __init__(self, yaml_data: str):
        self.yaml_data = yaml_data
        self.steps: List[TestStep] = []
        self._parse_yaml()

    def _parse_yaml(self):
        # Parse the YAML string
        data = yaml.safe_load(self.yaml_data)

        # Check if the parsed data is a list
        if not isinstance(data, list):
            raise ValueError("Invalid YAML format. Expected a top-level list.")

        for item in data:
            # Ensure each item has the required keys
            if not all(key in item for key in ["action", "expected_result"]):
                raise ValueError(f"Missing keys in item: {item}")

            # Create and append new item
            self.steps.append(
                TestStep(item["action"], item["expected_result"])
            )

    def get_items(self) -> List[TestStep]:
        return self.steps


class WindchillPartParser:
    def __init__(self, yaml_data: str):
        self.yaml_data = yaml_data
        self.wc_parts: List[WindchillPart] = []
        self._parse_yaml()

    def _parse_yaml(self):
        # Parse the YAML string
        data = yaml.safe_load(self.yaml_data)

        # Check if the parsed data is a list
        if not isinstance(data, list):
            raise ValueError("Invalid YAML format. Expected a top-level list.")

        for item in data:
            # Ensure each item has the required keys
            if not all(key in item for key in ["id", "part_name", "requirement_name"]):
                raise ValueError(f"Missing keys in item: {item}")

            # Create and append new item
            self.wc_parts.append(
                WindchillPart(item["id"], item["part_name"], item["requirement_name"])
            )

    def get_items(self) -> List[WindchillPart]:
        return self.wc_parts
