import logging
import os
import re
from pathlib import Path

import requests
import yaml
from datamodel_code_generator import generate, PythonVersion

LOGGER = logging.getLogger(__name__)


class SchemaLoader:
    def __init__(self, api_dict):
        self.api_dict = api_dict
        self.schema_cache = {}

    def get_refs(self, d):
        if isinstance(d, dict):
            for k, v in d.items():
                if isinstance(v, dict):
                    self.get_refs(v)
                elif isinstance(v, list):
                    for e in v:
                        self.get_refs(e)
                elif k == '$ref':
                    try:
                        schema_class = re.match(r'.*#/(\w+)$', v).groups()[0]
                    except AttributeError as e:
                        # no match, ref was something else (e.g., a parameter)
                        continue
                    d[k] = f'#/components/schemas/{schema_class}'
                    if v.startswith('https://') and schema_class not in self.schema_cache:
                        file_schema_classes = requests.get(v).json()
                        self.schema_cache.update(file_schema_classes)
                        LOGGER.info(f'Got schema for class {schema_class}')

    def load_schema(self):
        LOGGER.info('Starting schema loading')
        self.get_refs(self.api_dict)
        existing_classes = new_classes = set(self.schema_cache.keys())
        while new_classes:
            for c in new_classes:
                self.get_refs(self.schema_cache[c])
            new_classes = set(self.schema_cache.keys()) - existing_classes
            existing_classes = set(self.schema_cache.keys())


def create_model(model_file_name: str):
    strava_yaml = requests.get(
        url='https://converter.swagger.io/api/convert',
        params={'url': 'https://developers.strava.com/swagger/swagger.json'},
        headers={'Accept': 'application/yaml'},
        stream=True
    )
    api_dict = yaml.safe_load(strava_yaml.content)
    loader = SchemaLoader(api_dict)
    loader.load_schema()
    loader.api_dict['components']['schemas'] = loader.schema_cache
    generate(
        yaml.dump(loader.api_dict),
        output=Path(model_file_name),
        use_schema_description=True,
        use_field_description=True,
        target_python_version=PythonVersion.PY_38
    )
    LOGGER.info(f'Wrote model to file {model_file_name}')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    create_model(os.getenv('MODEL_FILE'))
