import os

from flask import Flask, Response, render_template

from src.screenshots_s3.s3_utils import list_s3_contents

app = Flask(__name__)


@app.route('/health-check', methods=['GET'])
def health_check():
    print('health check')
    return Response('', status=200)


BUCKET_NAME = os.getenv('BUCKET_NAME', '')
SCREENSHOTS_FOLDER_PREFIX = os.getenv('SCREENSHOTS_FOLDER_PREFIX', '').rstrip('/')
VIDEOS_FOLDER_PREFIX = os.getenv('VIDEOS_FOLDER_PREFIX', '').rstrip('/')


@app.route('/<commit_sha>')
def serve_images(commit_sha):
    html_page = render_template("serve_index.html", **{
        'images': get_html_images(commit_sha),
        'videos': get_html_videos(commit_sha),
    })

    return html_page


def get_html_images(commit_sha):
    folder_prefix = '{}/{}/screenshots'.format(SCREENSHOTS_FOLDER_PREFIX, commit_sha)
    all_files = list_s3_contents(BUCKET_NAME, folder_prefix)
    images = [{
        'src': 'http://{}.s3.eu-central-1.amazonaws.com/{}'.format(BUCKET_NAME, filename),
        'display_name': get_display_name(filename)
    } for filename in all_files]
    return images


def get_html_videos(commit_sha):
    folder_prefix = '{}/{}/videos'.format(VIDEOS_FOLDER_PREFIX, commit_sha)
    all_files = list_s3_contents(BUCKET_NAME, folder_prefix)
    print(all_files)
    videos = [{
        'src': 'http://{}.s3.eu-central-1.amazonaws.com/{}'.format(BUCKET_NAME, filename),
        'display_name': get_display_name(filename)
    } for filename in all_files]
    return videos


def get_display_name(filename):
    # no_prefix = filename.replace(SCREENSHOTS_FOLDER_PREFIX, '', 1)
    no_prefix = filename
    no_commit_hash = no_prefix[no_prefix.find('/', 1):]
    no_platform = no_commit_hash[no_commit_hash.find('/', 1):]
    return no_platform
