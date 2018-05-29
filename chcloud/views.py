# encoding=utf-8
from flask import request, jsonify, render_template, redirect, url_for
from flask.views import View, MethodView
from werkzeug.exceptions import BadRequest
from itsdangerous import URLSafeSerializer

import requests
from flask_login import login_user, login_required, current_user, logout_user

import cloudinary
import cloudinary.api
import cloudinary.uploader

from .config import (
    SLACK_OAUTH_STATE, SLACK_CLIENT_ID, SLACK_CLIENT_SECRET, SLACK_CH_TEAM_ID,
    CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET,
    SECRET_KEY
)
from .application import db, login_manager
from .models import User
from .forms import UploadForm, UploadEditForm, SettingsForm

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

        # Hide NSFW content
        if not current_user.show_nsfw:
            _to_pop = []
            for i, upload in enumerate(uploads):
                if 'nsfw' in upload['tags']:
                    _to_pop.append(i)
            for i in _to_pop:
                uploads.pop(i)

        for upload in uploads:
            if 'context' not in upload:
                upload['context'] = {
                    'custom': {
                        'title': upload['public_id'],
                        '_user': '',
                    }
                }
            try:
                _user_id = upload['context']['custom']['_user']
            except KeyError:
                _user_id = ''

            user = User.from_context(_user_id, mock=True)
            upload['context']['custom']['user'] = user

        return render_template('gallery.html', uploads=uploads)


class GalleryEdit(MethodView):
    endpoint = 'gallery_edit'
    decorators = [login_required]
    _serialiser = URLSafeSerializer(SECRET_KEY)

    def get(self, public_id=None):
        if public_id is None:
            # new upload
            form = UploadForm()
            tags_selected = []
        else:
            # existing upload
            form = UploadEditForm()
            res = cloudinary.api.resource(public_id)
            form.title.data = res['context']['custom']['title']
            tags_selected = res['tags']

        form.tags.choices = [('placeholder', 'placeholder')]

        return render_template('gallery_edit.html', form=form, public_id=public_id, tags_selected=tags_selected,
                               s_tags_selected=self._serialiser.dumps(tags_selected))

    def post(self, public_id=None):
        if public_id is None:
            # new upload
            form = UploadForm()
        else:
            form = UploadEditForm()

        s_tags_selected = request.form.get('s_tags_selected')
        tags_selected = self._serialiser.loads(s_tags_selected)

        if form.validate_on_submit():
            if public_id is None:
                # new upload
                cloudinary.uploader.upload(
                    form.image.data,
                    tags=form.tags.data,
                    context={
                        '_user': current_user.slack_id,
                        'title': form.title.data
                    }
                )
            else:
                # Edit existing upload, wait for the fun to start...
                if not form.tags.data and tags_selected != form.tags.data:
                    # aka tags are now empty and they weren't before => edit image, then delete all tags on it
                    cloudinary.uploader.explicit(public_id, context={
                        '_user': current_user.slack_id,
                        'title': form.title.data
                    }, type='upload')
                    cloudinary.uploader.remove_all_tags([public_id])
                else:
                    cloudinary.uploader.explicit(public_id, tags=form.tags.data, context={
                        '_user': current_user.slack_id,
                        'title': form.title.data
                    }, type='upload')
            return redirect(url_for(Gallery.endpoint))
        else:
            return render_template('gallery_edit.html', form=form, public_id=public_id, tags_selected=tags_selected,
                                   s_tags_selected=s_tags_selected)


class Settings(View):
    endpoint = 'settings'
    decorators = [login_required]

    def dispatch_request(self):
        form = SettingsForm()

        if not form.is_submitted():
            form.show_nsfw.data = current_user.show_nsfw

        if form.validate_on_submit():
            user = User.query.filter(User.id == current_user.id).first()
            user.show_nsfw = form.show_nsfw.data
            db.session.commit()
            return redirect(url_for(Gallery.endpoint))
        else:
            print(form.show_nsfw.errors, form.submit.errors)
            return render_template('settings.html', form=form)


class Logout(View):
    endpoint = 'logout'
    decorators = [login_required]

    def dispatch_request(self):
        logout_user()
        return redirect(url_for('index'))


class APITags(View):
    endpoint = 'api_tags'
    decorators = [login_required]

    def dispatch_request(self):
        tags = cloudinary.api.tags()['tags']
        tags = [tag for tag in tags if not tag.startswith('user:')]

        return jsonify({
            'results': [{'id': tag, 'text': tag} for tag in tags]
        })
