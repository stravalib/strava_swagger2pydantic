import logging
import os
import re
from pathlib import Path

import requests
import yaml
from datamodel_code_generator import generate, PythonVersion, LiteralType

LOGGER = logging.getLogger(__name__)


class SchemaLoader:
    def __init__(self, api_dict):
        self.api_dict = api_dict
        self.schema_cache = {}

    def get_external_schema_components(self, partial_schema):
        """
        Recursively searches and retrieves external schema components
        (following `$ref` keys).
        :param partial_schema: part of schema in which to search for
                               externally defined components
        :return: None (updates `self.schema_cache`)
        """
        if isinstance(partial_schema, dict):
            for key, value in partial_schema.items():
                if isinstance(value, dict):
                    self.get_external_schema_components(value)
                elif isinstance(value, list):
                    for e in value:
                        self.get_external_schema_components(e)
                elif key == "$ref":
                    try:
                        # assume value is a url `https://[HOST]/swagger/any.json#/[SCHEMA_CLASS]`
                        schema_class = re.match(r".*#/(\w+)$", value).groups()[
                            0
                        ]
                    except AttributeError:
                        # no match, ref was something else (e.g., a parameter)
                        continue
                    # replace external ref to internal schema component

                    partial_schema[
                        key
                    ] = f"#/components/schemas/{schema_class}"

                    if (
                        value.startswith("https://")
                        and schema_class not in self.schema_cache
                    ):
                        # schema class definition is not yet known, retrieve it
                        file_schema_classes = requests.get(value).json()
                        self.schema_cache.update(file_schema_classes)
                        LOGGER.info(
                            f"Got schema for class(es) "
                            f'{", ".join(list(file_schema_classes.keys()))}'
                        )

    def load_schema(self):
        LOGGER.info("Starting schema loading")
        self.get_external_schema_components(self.api_dict)
        existing_classes = new_classes = set(self.schema_cache.keys())
        while new_classes:
            for c in new_classes:
                self.get_external_schema_components(self.schema_cache[c])
            new_classes = set(self.schema_cache.keys()) - existing_classes
            existing_classes = set(self.schema_cache.keys())


def create_model(model_file_name: str):
    strava_yaml = requests.get(
        url="https://converter.swagger.io/api/convert",
        params={"url": "https://developers.strava.com/swagger/swagger.json"},
        headers={"Accept": "application/yaml"},
        stream=True,
    )
    api_dict = yaml.safe_load(strava_yaml.content)
    loader = SchemaLoader(api_dict)
    loader.load_schema()
    loader.api_dict["components"]["schemas"] = loader.schema_cache
    generate(
        yaml.dump(loader.api_dict),
        output=Path(model_file_name),
        use_schema_description=True,
        use_field_description=True,
        target_python_version=PythonVersion.PY_39,
        disable_timestamp=True,
        enum_field_as_literal=LiteralType.All,
        use_double_quotes=True,
        field_constraints=True,
    )
    LOGGER.info(f"Wrote model to file {model_file_name}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    create_model(os.getenv("MODEL_FILE"))
