#!/usr/bin/env python3

import logging
from fhirclient import client
from fhirclient.models.medication import Medication
from fhirclient.models.medicationrequest import MedicationRequest

from flask import Flask, request, redirect, session

# app setup
smart_defaults = {
    'app_id': 'my_web_app',
    'api_base': None,
    'redirect_uri': 'http://localhost:8000/fhir-app/',
}

app = Flask(__name__)

def _save_state(state):
    session['state'] = state

def _get_smart():
    state = session.get('state')
    if state:
        return client.FHIRClient(state=state, save_func=_save_state)
    elif smart_defaults['api_base']:
        return client.FHIRClient(settings=smart_defaults, save_func=_save_state)
    else:
        return None

def _logout():
    if 'state' in session:
        smart = _get_smart()
        smart.reset_patient()

def _reset():
    if 'state' in session:
        del session['state']

def _get_prescriptions(smart):
    search = MedicationRequest.where({'patient': smart.patient_id})
    return list(search.perform_resources_iter(smart.server))

def _get_medication_by_ref(ref, smart):
    med_id = ref.split("/")[1]
    return Medication.read(med_id, smart.server).code

def _med_name(med):
    if med.coding:
        name = next((coding.display for coding in med.coding if coding.system == 'http://www.nlm.nih.gov/research/umls/rxnorm'), None)
        if name:
            return name
    if med.text and med.text:
        return med.text
    return "Unnamed Medication(TM)"

def _get_med_name(prescription, client=None):
    if prescription.medicationCodeableConcept is not None:
        med = prescription.medicationCodeableConcept
        return _med_name(med)
    elif prescription.medicationReference is not None and client is not None:
        med = _get_medication_by_ref(prescription.medicationReference.reference, client)
        return _med_name(med)
    else:
        return 'Error: medication not found'

# views

@app.route('/')
@app.route('/index.html')
def index():
    smart = _get_smart()
    body = "<h1>Hello</h1>"

    if smart is None:
        body += "<p>Please set api_base.</p>"

    elif smart.ready and smart.patient is not None:
        name = smart.human_name(
            smart.patient.name[0] if smart.patient.name else 'Unknown'
        )

        body += f"<p>You are authorized for {name}.</p>"

        pres = _get_prescriptions(smart)
        if pres:
            body += "<ul>"
            body += "".join(f"<li>{_get_med_name(p, smart)}</li>" for p in pres)
            body += "</ul>"
        else:
            body += "<p>No prescriptions found.</p>"

        body += '<p><a href="/logout">Change patient</a></p>'

    else:
        try:
            smart.prepare()
            auth_url = smart.authorize_url
        except Exception as e:
            return f"<h1>SMART Error</h1><pre>{e}</pre>"

        if auth_url:
            body += f'<p>Please <a href="{auth_url}">authorize</a>.</p>'
        else:
            body += "<p>Running against a no-auth server.</p>"

    body += '<p><a href="/reset">Reset</a></p>'
    return body

@app.route('/fhir-app/')
def callback():
    """ OAuth2 callback interception.
    """
    smart = _get_smart()
    try:
        smart.handle_callback(request.url)
    except Exception as e:
        return """<h1>Authorization Error</h1><p>{0}</p><p><a href="/">Start over</a></p>""".format(e)
    return redirect('/')


@app.route('/logout')
def logout():
    _logout()
    return redirect('/')


@app.route('/reset')
def reset():
    _reset()
    return redirect('/')


# start the app
if '__main__' == __name__:
   
    
    logging.basicConfig(level=logging.DEBUG)
    app.run(debug=True, port=8000)