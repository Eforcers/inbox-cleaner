# -*- coding: utf-8 -*-
"""
views.py

URL route handlers

Note that any handler params must match the URL route params.
For example the *say_hello* handler, handling the URL route '/hello/<username>',
  must be passed *username* as the argument.

"""
import logging

from google.appengine.api import users
from google.appengine.api.datastore_errors import BadValueError
from google.appengine.datastore.datastore_query import Cursor
from google.appengine.ext import deferred

from helpers import OAuthDanceHelper, DirectoryHelper, IMAPHelper
from flask import request, render_template, url_for, redirect, abort, g
from flask_cache import Cache
from inbox import app, constants
from decorators import login_required
from tasks import generate_count_report, schedule_user_move, \
    schedule_user_cleaning
from forms import CleanUserProcessForm, MoveProssessForm
from models import CleanUserProcess, MoveProcess

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


@app.route('/_ah/start')
def start():
    """App Engine start handler
    """
    return ''


@app.route('/')
def index():
    return 'Landing Page'


@app.route('/admin')
@app.route('/admin/')
def admin_index():
    return redirect(url_for('list_process'))


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


@app.route('/process/', methods=['GET', 'POST'])
@login_required
def list_process():
    form = CleanUserProcessForm()
    user = users.get_current_user()
    clean_process_saved = False

    clean_processes = []
    clean_process_query = CleanUserProcess.query().order()
    query_params = {}
    if request.method == 'POST':
        if form.validate_on_submit():
            imap = IMAPHelper()
            logged_in, _ = imap.login(
                form.data['source_email'], form.data['source_password'])
            imap.close()

            if logged_in != 'OK':
                form.source_email.errors.append(
                    "Can access the email with those credentials")
            else:
                clean_user_process = CleanUserProcess(
                    owner_email=user.email(),
                    destination_message_email=user.email(),
                    status=constants.STARTED
                )
                for key, value in form.data.iteritems():
                    setattr(clean_user_process, key, value)
                clean_process_key = clean_user_process.put()
                clean_process_saved = True
                # TODO: process does not appears immediately after it's saved
                # launch Pipeline
                deferred.defer(schedule_user_cleaning,
                               user_email=form.data['source_email'],
                               clean_process_key=clean_process_key)

    is_prev = request.args.get('prev', False)
    url_cursor = request.args.get('cursor', None)
    cursor = Cursor(urlsafe=url_cursor) if url_cursor else None

    if is_prev:
        clean_process_query = clean_process_query.order(
            CleanUserProcess.created)
        cursor = cursor.reversed()
    else:
        clean_process_query = clean_process_query.order(
            -CleanUserProcess.created)

    data, next_curs, more = clean_process_query.fetch_page(
        constants.PAGE_SIZE, start_cursor=cursor)
    clean_processes.extend(data)

    if is_prev:
        prev_curs = next_curs.reversed().urlsafe() if more else None
        next_curs = url_cursor
    else:
        prev_curs = url_cursor
        next_curs = next_curs.urlsafe() if more else None

    return render_template('process.html', form=form, user=user.email(),
                           clean_process_saved=clean_process_saved,
                           clean_processes=clean_processes, next_curs=next_curs,
                           more=more, prev_curs=prev_curs)


@app.route('/process/move', methods=['GET', 'POST'])
@login_required
def move_process():
    form = MoveProssessForm()
    user = users.get_current_user()
    process_id = None
    if request.method == 'POST':
        if form.validate_on_submit():
            try:
                move_process = MoveProcess(ok_count=0, error_count=0,
                                           total_count=0)
                emails = list(set([
                    email.strip() for email in form.data['emails']
                        .splitlines()]))
                if len(emails) > 0:
                    move_process.emails = emails
                    move_process.tag = form.data['tag']
                    move_process_key = move_process.put()
                    for email in emails:
                        deferred.defer(schedule_user_move, user_email=email,
                                       tag=move_process.tag,
                                       move_process_key=move_process_key)
                    process_id = move_process_key.id()
                else:
                    form.errors['Emails'] = ['Emails should not be empty']
            except BadValueError, e:
                logging.exception('error saving process')
                form.errors['Emails'] = ['Emails are malformed']

    return render_template('move_process.html', form=form, user=user.email(),
                           process_id=process_id)


@app.route('/cron/process/count')
def count_report():
    deferred.defer(generate_count_report)
    return 'Count report is being generated...'


# # Error handlers
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

