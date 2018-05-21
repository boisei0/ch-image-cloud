# encoding=utf-8
from flask import request, jsonify
from flask.views import View
from werkzeug.exceptions import BadRequest

import requests

from .config import SLACK_OAUTH_STATE, SLACK_CLIENT_ID, SLACK_CLIENT_SECRET


class OAuthRedirect(View):
    endpoint = 'oauth_redirect'

    def dispatch_request(self):
        if request.args.get('state') != SLACK_OAUTH_STATE:
            raise BadRequest()

        r = requests.post('https://slack.com/api/oauth.access', data={
            'client_id': SLACK_CLIENT_ID,
            'client_secret': SLACK_CLIENT_SECRET,
            'code': request.args.get('code')
        })

        data = r.json()

        if not data['ok']:
            # TODO: Handle error
            return jsonify(data)

        return "DEBUG: {user_id}, {access_token}".format(**data)
