# -*- coding: utf-8 -*-
from inbox.helpers import MandrillHelper
from inbox.models import Client


def send_birthday_message(user):
    """
    This is the actual method that sends the email message to the user
    :param user: user object to merge in the birthday template
    """
    client = Client.get()

    mandrill_helper = MandrillHelper(api_key=client.mandrill_key)

    merge_dict = {
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
        'thumbnail_photo_url': user.thumbnail_photo_url,
        'gender': user.gender
    }

    message = MandrillHelper.build_message(
        merge_dict=merge_dict,
        subject=client.subject,
        from_email=client.from_email,
        from_name=client.from_name,
        to_email=user.email,
        to_name="%s %s" %(user.first_name, user.last_name),
        tags=client.tags
    )

    mandrill_helper.send(message, client.mandrill_template)
