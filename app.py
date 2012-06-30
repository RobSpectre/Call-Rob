import os
import signal

from flask import Flask
from flask import render_template
from flask import request

from twilio import twiml
from twilio.rest import TwilioRestClient
from twilio.util import TwilioCapability


# Declare and configure application
app = Flask(__name__, static_url_path='/static')
app.config.from_pyfile('local_settings.py')


# Call Rob
@app.route('/voice', methods=['GET', 'POST'])
def voice():
    response = twiml.Response()
    if request.form['From'] == 'client:kristina':
        dial = response.dial(callerId=app.config['TWILIO_CALLER_ID'])
    else:
        dial = response.dial()
    dial.number(app.config['CURRENT_NUMBER'])
    return str(response)


# SMS Rob
@app.route('/sms', methods=['GET', 'POST'])
def sms():
    response = twiml.Response()
    client = TwilioRestClient(app.config['TWILIO_ACCOUNT_SID'],
        app.config['TWILIO_AUTH_TOKEN'])
    client.sms.messages.create(from_=app.config['TWILIO_CALLER_ID'],
            to=app.config['CURRENT_NUMBER'], body="%s: %s" %
                (request.form['From'], request.form['Body']))
    return str(response)


# Call Rob via web browser
@app.route('/')
def index():
    configuration_error = None
    for key in ('TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN', 'TWILIO_APP_SID',
            'TWILIO_CALLER_ID'):
        if not app.config[key]:
            configuration_error = "Missing from local_settings.py: " \
                    "%s" % key
            token = None
    if not configuration_error:
        token = generateClientToken(app.config['TWILIO_ACCOUNT_SID'],
                app.config['TWILIO_AUTH_TOKEN'])
    return render_template('index.html', token=token,
            configuration_error=configuration_error)


# Generate Twilio Client token for mobile apps
@app.route('/token')
def token():
    token = generateClientToken(app.config['TWILIO_ACCOUNT_SID'],
        app.config['TWILIO_AUTH_TOKEN'])
    return token


def generateClientToken(account_sid, auth_token):
    capability = TwilioCapability(account_sid, auth_token)
    capability.allow_client_incoming("kristina")
    capability.allow_client_outgoing(app.config['TWILIO_APP_SID'])
    return capability.generate()


# Handles SIGTERM so that we don't get an error when Heroku wants or needs to
# restart the dyno
def graceful_shutdown(signum, frame):
    exit()

signal.signal(signal.SIGTERM, graceful_shutdown)


# If PORT not specified by environment, assume development config.
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    if port == 5000:
        app.debug = True
    app.run(host='0.0.0.0', port=port)
