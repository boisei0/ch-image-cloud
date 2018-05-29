# encoding=utf-8
from collections import namedtuple

from flask import request, jsonify, render_template, redirect, url_for
from flask.views import View, MethodView
from werkzeug.exceptions import BadRequest

import requests
from flask_login import login_user, login_required, current_user

import cloudinary
import cloudinary.api
import cloudinary.uploader

from .config import (
    SLACK_OAUTH_STATE, SLACK_CLIENT_ID, SLACK_CLIENT_SECRET, SLACK_CH_TEAM_ID,
    CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET
)
from .application import db, login_manager
from .models import User
from .forms import UploadForm, UploadEditForm

cloudinary.config(cloud_name=CLOUDINARY_CLOUD_NAME, api_key=CLOUDINARY_API_KEY, api_secret=CLOUDINARY_API_SECRET)


@login_manager.unauthorized_handler
def unauthorised_handler():
    return redirect(
        'https://slack.com/oauth/authorize?scope=identity.basic&client_id={client_id}&state={state}'.format(
            client_id=SLACK_CLIENT_ID,
            state=SLACK_OAUTH_STATE
        )
    )


class Index(View):
    endpoint = 'index'

    def dispatch_request(self):
        return render_template('index.html', client_id=SLACK_CLIENT_ID, state=SLACK_OAUTH_STATE)


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

        if data['team']['id'] != SLACK_CH_TEAM_ID:
            return "Sorry this application is limited to users from Clexa Haven"

        user = User.query.filter(User.slack_id == data['user']['id']).first()
        if user:
            # Update display name
            user.display_name = data['user']['name']
        else:
            # First login
            user = User(data['user']['name'], data['access_token'], data['user']['id'])
            db.session.add(user)

        db.session.commit()

        login_user(user)

        return redirect(url_for(Gallery.endpoint))


class Gallery(View):
    endpoint = 'gallery'
    decorators = [login_required]

    def dispatch_request(self):
        uploads = cloudinary.api.resources(tags=True, context=True)['resources']

        # # preprocess uploads:
        # for upload in uploads:
        #     _to_pop = None
        #     for tag in upload['tags']:
        #         if tag.startswith('user:'):
        #             try:
        #                 user = User.from_tag(tag)
        #             except ValueError:
        #                 # mock user
        #                 _user = namedtuple('User', ['display_name'])
        #                 user = _user('Unknown user')
        #             if 'context' not in upload:
        #                 upload['context'] = {
        #                     'custom': {
        #                         '_user': user.display_name
        #                     }
        #                 }
        #             else:
        #                 upload['context']['custom']['_user'] = user.display_name
        #             _to_pop = tag
        #             break
        #     if _to_pop:
        #         upload['tags'].remove(_to_pop)

        for upload in uploads:
            if 'context' not in upload:
                upload['context'] = {
                    'custom': {
                        'title': upload['public_id'],
                        '_user': '',
                    }
                }

            user = User.from_context(upload['context']['custom']['_user'], mock=True)
            upload['context']['custom']['user'] = user

        return render_template('gallery.html', uploads=uploads)


class GalleryEdit(MethodView):
    endpoint = 'gallery_edit'
    decorators = [login_required]

    def get(self, public_id=None):
        if public_id is None:
            # new upload
            form = UploadForm()
        else:
            # existing upload
            form = UploadEditForm()
            res = cloudinary.api.resource(public_id)
            form.title.data = res['context']['custom']['title']

        return render_template('gallery_edit.html', form=form, public_id=public_id)

    def post(self, public_id=None):
        form = UploadForm()

        if form.validate_on_submit():
            if public_id is None:
                # new upload
                # TODO: continue here
                cloudinary.uploader.upload(form.image.data)


class APITags(View):
    endpoint = 'api_tags'
    decorators = [login_required]

    def dispatch_request(self):
        tags = cloudinary.api.tags()['tags']
        tags = [tag for tag in tags if not tag.startswith('user:')]

        return jsonify({
            'results': [{'id': tag, 'text': tag} for tag in tags]
        })
