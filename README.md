# Strava Swagger to Pydantic
This repo support a Github Action that creates a Pydantic model from 
Strava's [Swagger API](https://developers.strava.com/playground/) definition.

The script is run via a nightly cron job [in this GitHub action](https://github.com/stravalib/stravalib/blob/main/.github/workflows/check-strava-api.yml). The action creates an new module called  [strava_model.py module](https://github.com/stravalib/stravalib/blob/main/src/stravalib/strava_model.py) that represents the most recent version of Strava's swagger.json file.

## How to run this locally

1. First, make sure you have all of the necessary requirements installed. We are using the [datamodel-code-generator](https://docs.pydantic.dev/latest/integrations/datamodel_code_generator/) package to generate the model.

```bash
pip install requirements.txt
```

2. Once the requirements are installed, you are ready to run the script.

This module takes one input environment variable - the name of the 
output module. You can either store this value as an environment variable 
called `MODEL_FILE` on your computer. Or you can define it in place as 
follows:

```bash
# Run this in the terminal with your python environment activated
$ MODEL_FILE="output_model.py" python swagger2pydantic.py
```

In the example above, the script will run, creating a new module called 
output_model.py in your current working directory. 
