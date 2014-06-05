"""
forms.py

Web forms based on Flask-WTForms

See: http://flask.pocoo.org/docs/patterns/wtforms/
     http://wtforms.simplecodes.com/

"""

from flaskext import wtf
from flaskext.wtf import validators
from wtforms.ext.appengine.ndb import model_form
from models import CleanUserProcess

CleanUserProcessForm = model_form(CleanUserProcess, wtf.Form,field_args={
    'source_email': dict(validators=[validators.Required(),validators.Email()]),
    'source_password': dict(validators=[validators.Required()]),
    'destination_message_email': dict(validators=[validators.Required(),validators.Email()]),
})