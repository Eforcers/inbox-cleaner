# -*- coding: utf-8 -*-
"""
views.py

URL route handlers

Note that any handler params must match the URL route params.
For example the *say_hello* handler, handling the URL route '/hello/<username>',
  must be passed *username* as the argument.

"""
from csv import DictReader
import logging
from datetime import datetime

from google.appengine.api import users, namespace_manager, memcache
from google.appengine.ext import deferred
from google.appengine.runtime.apiproxy_errors import CapabilityDisabledError
from google.appengine.ext.db.metadata import get_namespaces

from forms import BirthdayFileForm
from helpers import OAuthDanceHelper, DirectoryHelper
from models import get_birthdays, Client, User
from flask import request, render_template, flash, url_for, redirect, abort, g
from flask_cache import Cache
from inbox import app, constants
from decorators import login_required, admin_required
from forms import ExampleForm
from models import ExampleModel
from tasks import send_birthday_message


# Flask-Cache (configured to use App Engine Memcache API)
cache = Cache(app)


@app.before_request
def before_request():
    if request.path == url_for('warmup'):
        return
    user = users.get_current_user()
    if user:
        g.logout_text = 'Logout'
        g.url_logout = users.create_logout_url(url_for('admin_index'))
        g.user_email = user.email()
    else:
        g.logout_text = 'Login'
        g.url_logout = users.create_login_url(url_for('admin_index'))
        g.user_email = None
    g.menu = []
    for endpoint, name in constants.MENU_ITEMS:
        g.menu.append({
            'is_active': request.path == url_for(endpoint),
            'url': url_for(endpoint),
            'name': name,
        })


@app.route('/_ah/warmup')
def warmup():
    """App Engine warmup handler
    See http://code.google.com/appengine/docs/python/config/appconfig.html#Warming_Requests

    """
    return ''

@app.route('/')
def index():
    return redirect(url_for('list_process'))


@app.route('/admin/', methods=['GET'])
@admin_required
def admin_index():
    """This view requires an admin account"""
    return 'Super-seekrit admin page.'


@app.route('/admin/settings/', methods=['GET', 'POST'])
@admin_required
def settings():
    if request.method == 'POST':
        pass
    return render_template('settings.html')


@app.route('/setup/', methods=['GET'])
@login_required
def set_up():
    """
    Handle the installation process for a new domain
    :return: Redirect URL for OAuth
    """
    domain = request.args.get('domain', None)
    # TODO: Check domain is valid and user is admin in apps
    client = Client.get_instance()
    admin_email = users.get_current_user().email()
    if not client:
        #If there is no client object, create it
        Client(id=1, primary_domain_name=domain,
               administrators=[admin_email], reply_to=admin_email).put()

    return redirect(url_for('start_oauth2_dance'))


@app.route('/oauth/start/', methods=['GET'])
@login_required
def start_oauth2_dance(domain):
    client = Client.get_instance()
    login_hint = users.get_current_user().email()
    approval_prompt = 'auto' if client.refresh_token else 'force'
    scope = constants.OAUTH2_SCOPES
    redirect_uri = url_for('oauth_callback', _external=True)
    oauth_helper = OAuthDanceHelper(scope=scope, redirect_uri=redirect_uri,
                                    approval_prompt=approval_prompt)
    url = oauth_helper.step1_get_authorize_url()
    # TODO: Add a random token to avoid forgery
    return redirect("%s?login_hint=%s" % (url, login_hint))


@app.route('/oauth/callback/', methods=['GET'])
def oauth_callback(self):
    code = request.args.get('code', None)
    if not code:
        logging.error('No code, no authorization')
        abort(500)
    redirect_uri = url_for('oauth_callback', _external=True)
    oauth_helper = OAuthDanceHelper(redirect_uri=redirect_uri)
    credentials = oauth_helper.step2_exchange(code)
    client = Client.get_instance()
    client.credentials = credentials.to_json()
    if credentials.refresh_token:
        client.refresh_token = credentials.refresh_token
    directory_helper = DirectoryHelper(client.credentials, None,
                                       client.refresh_token)
    client.customer_id = directory_helper.get_customer_id(
        client.administrators[0]
    )
    client.put()
    return redirect(url_for('settings'))


@app.route('/admin/birthdays/upload', methods=['GET', 'POST'])
@admin_required
def upload_csv():
    form = BirthdayFileForm()
    if form.validate_on_submit() and form.birthday_file.data:
        file_request = request.files[form.birthday_file.name]
        # Process CSV file
        input_file = DictReader(csvfile=file_request.read(),
                                fieldnames=constants.BIRTHDAY_CSV_COLUMNS)
        #TODO: Validate both columns are required. Feedback on errors
        User.add_many_birthdays(input_file)
        flash(u'File successfully uploaded.', 'success')

    return render_template('upload.html', form=form)


@app.route('/admin/birthdays/template/', methods=['GET'])
@admin_required
def get_csv_template():
    pass


@app.route('/process/', methods=['GET', 'POST'])
@admin_required
def list_process():
    birthdays = User.get_all_birthdays()
    return render_template('list_birthdays.html', birthdays=birthdays)


@app.route('/admin/birthdays/<int:birthday_id>/edit/', methods=['GET', 'POST'])
@admin_required
def edit_birthday(birthday_id):
    example = ExampleModel.get_by_id(birthday_id)
    form = ExampleForm(obj=example)
    if request.method == "POST":
        if form.validate_on_submit():
            example.example_name = form.data.get('example_name')
            example.example_description = form.data.get('example_description')
            example.put()
            flash(u'Example %s successfully saved.' % birthday_id, 'success')
            return redirect(url_for('list_examples'))
    return render_template('edit_birthday.html', example=example, form=form)






# TODO: Remove examples from before, below this line

@login_required
def list_examples():
    """List all examples"""
    examples = ExampleModel.query()
    form = ExampleForm()
    if form.validate_on_submit():
        example = ExampleModel(
            example_name=form.example_name.data,
            example_description=form.example_description.data,
            added_by=users.get_current_user()
        )
        try:
            example.put()
            example_id = example.key.id()
            flash(u'Example %s successfully saved.' % example_id, 'success')
            return redirect(url_for('list_examples'))
        except CapabilityDisabledError:
            flash(u'App Engine Datastore is currently in read-only mode.',
                  'info')
            return redirect(url_for('list_examples'))
    return render_template('list_examples.html', examples=examples, form=form)


@login_required
def edit_example(example_id):
    example = ExampleModel.get_by_id(example_id)
    form = ExampleForm(obj=example)
    if request.method == "POST":
        if form.validate_on_submit():
            example.example_name = form.data.get('example_name')
            example.example_description = form.data.get('example_description')
            example.put()
            flash(u'Example %s successfully saved.' % example_id, 'success')
            return redirect(url_for('list_examples'))
    return render_template('edit_example.html', example=example, form=form)


@login_required
def delete_example(example_id):
    """Delete an example object"""
    example = ExampleModel.get_by_id(example_id)
    try:
        example.key.delete()
        flash(u'Example %s successfully deleted.' % example_id, 'success')
        return redirect(url_for('list_examples'))
    except CapabilityDisabledError:
        flash(u'App Engine Datastore is currently in read-only mode.', 'info')
        return redirect(url_for('list_examples'))


## Error handlers
# Handle 404 errors
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# Handle 500 errors
@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

# Handle 403 errors
@app.errorhandler(403)
def unauthorized(e):
    return render_template('403.html'), 403

