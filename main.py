from fhirclient import client
from fhirclient import server

from fhirclient.models.patient import Patient
from fhirclient.models.encounter import Encounter
from fhirclient.models.procedure import Procedure
from fhirclient.models.humanname import HumanName
from fhirclient.models.observation import Observation

import json

print("=== START ===")

# ---------------------------------
# SMART on FHIR Client
# ---------------------------------

settings = {
    'app_id': 'my_web_app',
    'api_base': 'https://r4.smarthealthit.org'
}

smart = client.FHIRClient(settings=settings)

print("ready:", smart.ready)

# ---------------------------------
# Read Patient
# ---------------------------------

print("\n=== PATIENT ===")

patient_id = '2cda5aad-e409-4070-9a15-e1c35c46ed5a'

patient = Patient.read(
    patient_id,
    smart.server
)

print("Patient ID:", patient.id)
print("Birth Date:", patient.birthDate.isostring)
print("Name:", smart.human_name(patient.name[0]))

# ---------------------------------
# Direct FHIRServer Access
# ---------------------------------

print("\n=== DIRECT SERVER ===")

srv = server.FHIRServer(
    None,
    'https://r4.smarthealthit.org'
)

patient2 = Patient.read(patient_id, srv)

print("Given Name:", patient2.name[0].given)

# ---------------------------------
# Encounter Search
# ---------------------------------

print("\n=== ENCOUNTERS ===")

search = Encounter.where(struct={
    'subject': patient_id
})

encounters = list(
    search.perform_resources_iter(smart.server)
)

for enc in encounters:
    print("Encounter ID:", enc.id)

# ---------------------------------
# Include Patient Resource
# ---------------------------------

print("\n=== INCLUDE SUBJECT ===")

search_include = search.include('subject')

results_include = list(
    search_include.perform_resources_iter(smart.server)
)

for res in results_include:
    print("Resource Type:", res.resource_type)

# ---------------------------------
# Reverse Include Procedure
# ---------------------------------

print("\n=== REVERSE INCLUDE PROCEDURE ===")

search_rev = search.include(
    'encounter',
    Procedure,
    reverse=True
)

results_rev = list(
    search_rev.perform_resources_iter(smart.server)
)

for res in results_rev:
    print("Resource Type:", res.resource_type)

# ---------------------------------
# Raw Bundle Access
# ---------------------------------

print("\n=== RAW BUNDLES ===")

bundles = search_rev.perform_iter(smart.server)

for bundle in bundles:
    if bundle.entry:
        for entry in bundle.entry:
            print(
                "Bundle Resource:",
                entry.resource.resource_type
            )

# ---------------------------------
# Observation Search
# ---------------------------------

print("\n=== OBSERVATIONS ===")

obs_search = Observation.where(struct={
    'patient': patient_id
})

observations = list(
    obs_search.perform_resources_iter(smart.server)
)

for obs in observations[:5]:
    print("Observation ID:", obs.id)

# ---------------------------------
# Create Patient Object
# ---------------------------------

print("\n=== CREATE PATIENT OBJECT ===")

new_patient = Patient({
    'id': 'patient-1'
})

print("New Patient ID:", new_patient.id)

name = HumanName()

name.given = ['Peter']
name.family = 'Parker'

new_patient.name = [name]

print(new_patient.as_json())

# ---------------------------------
# JSON Parsing
# ---------------------------------

print("\n=== JSON PARSING ===")

pjs = json.loads('''
{
    "name": [
        {
            "given": ["Peter"]
        }
    ],
    "resourceType": "Patient"
}
''')

json_patient = Patient(pjs)

print(json_patient.name[0].given)

# ---------------------------------
# Validation Error Example
# ---------------------------------

print("\n=== VALIDATION ERROR EXAMPLE ===")

try:
    bad_name = HumanName()

    # WRONG: should be list
    bad_name.given = "Peter"

    bad_patient = Patient({
        'id': 'bad-patient'
    })

    bad_patient.name = [bad_name]

    print(bad_patient.as_json())

except Exception as e:
    print("Validation Error:")
    print(e)

# ---------------------------------
# Done
# ---------------------------------

print("\n=== DONE ===")

git clone https://github.com/smart-on-fhir/client-py.git
cd client-py/demos/flask
python3 -m venv env
. env/bin/activate
pip install -r requirements.txt
# Edit flask_app.py and put your own server's URL as api_base.
./flask_app.py