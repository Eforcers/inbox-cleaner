# -*- coding: utf-8 -*-
import base64
import hashlib
import hmac
import random
import time
import urllib


def chunkify(l, n):
    n = n if n < len(l) else len(l)
    c = len(l)/n + 1
    return [l[i:i+c] for i in range(0, len(l), c)]

class OAuthEntity(object):
    """Represents consumers and tokens in OAuth."""

    def __init__(self, key, secret):
        self.key = key
        self.secret = secret


def EscapeAndJoin(elems):
    return '&'.join([UrlEscape(x) for x in elems])


def FormatUrlParams(params):
    """Formats parameters into a URL query string.

    Args:
      params: A key-value map.

    Returns:
      A URL query string version of the given parameters.
    """
    param_fragments = []
    for param in sorted(params.iteritems(), key=lambda x: x[0]):
        param_fragments.append('%s=%s' % (param[0], UrlEscape(param[1])))
    return '&'.join(param_fragments)


def UrlEscape(text):
    # See OAUTH 5.1 for a definition of which characters need to be escaped.
    return urllib.quote(text, safe='~-._')


def GenerateOauthSignature(base_string, consumer_secret, token_secret=''):
    key = EscapeAndJoin([consumer_secret, token_secret])
    return GenerateHmacSha1Signature(base_string, key)


def GenerateHmacSha1Signature(text, key):
    digest = hmac.new(key, text, hashlib.sha1)
    return base64.b64encode(digest.digest())


def GenerateSignatureBaseString(method, request_url_base, params):
    """Generates an OAuth signature base string.

    Args:
      method: The HTTP request method, e.g. "GET".
      request_url_base: The base of the requested URL. For example, if the
        requested URL is
        "https://mail.google.com/mail/b/xxx@domain.com/imap/?" +
        "xoauth_requestor_id=xxx@domain.com", the request_url_base would be
        "https://mail.google.com/mail/b/xxx@domain.com/imap/".
      params: Key-value map of OAuth parameters, plus any parameters from the
        request URL.

    Returns:
      A signature base string prepared according to the OAuth Spec.
    """
    return EscapeAndJoin([method, request_url_base, FormatUrlParams(params)])


def FillInCommonOauthParams(params, consumer):
    """Fills in parameters that are common to all oauth requests.

    Args:
      params: Parameter map, which will be added to.
      consumer: An OAuthEntity representing the OAuth consumer.
    """

    params['oauth_consumer_key'] = consumer.key
    params['oauth_nonce'] = str(random.randrange(2 ** 64 - 1))
    params['oauth_signature_method'] = 'HMAC-SHA1'
    params['oauth_version'] = '1.0'
    params['oauth_timestamp'] = str(int(time.time()))


def GenerateXOauthString(consumer, xoauth_requestor_id, method, protocol):
    """Generates an IMAP XOAUTH authentication string.

    Args:
      consumer: An OAuthEntity representing the consumer.
      xoauth_requestor_id: The Google Mail user who's inbox will be
                           searched (full email address)
      method: The HTTP method used in the API request
      protocol: The protocol used in the API request

    Returns:
      A string that can be passed as the argument to an IMAP
      "AUTHENTICATE XOAUTH" command after being base64-encoded.
    """

    url_params = {}
    url_params['xoauth_requestor_id'] = xoauth_requestor_id
    oauth_params = {}
    FillInCommonOauthParams(oauth_params, consumer)

    signed_params = oauth_params.copy()
    signed_params.update(url_params)
    request_url_base = (
        'https://mail.google.com/mail/b/%s/%s/' % (
            xoauth_requestor_id, protocol))
    base_string = GenerateSignatureBaseString(
        method,
        request_url_base,
        signed_params)

    oauth_params['oauth_signature'] = GenerateOauthSignature(base_string,
                                                             consumer.secret)

    # Build list of oauth parameters
    formatted_params = []
    for k, v in sorted(oauth_params.iteritems()):
        formatted_params.append('%s="%s"' % (k, UrlEscape(v)))
    param_list = ','.join(formatted_params)

    # Append URL parameters to request url, if present
    if url_params:
        request_url = '%s?%s' % (request_url_base,
                                 FormatUrlParams(url_params))
    else:
        request_url = request_url_base

    return '%s %s %s' % (method, request_url, param_list)

