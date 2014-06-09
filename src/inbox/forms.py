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
    'name':dict(validators=[validators.Required()]),
    'source_email': dict(validators=[validators.Required(),validators.Email()]),
    'source_password': dict(validators=[validators.Required()]),
    'search_criteria': dict(validators=[validators.Required()]),
},exclude=['destination_message_email','owner_email',
           'credentials','refresh_token','status','pipeline_id'] )


class MoveProssessForm(wtf.Form):
    emails = wtf.TextAreaField('emails', validators=[validators.Required()])
    tag = wtf.TextField('tag', validators=[validators.Required()])