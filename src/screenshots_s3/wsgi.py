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


@app.route('/<commit_sha>')
def serve_images(commit_sha):
    folder_prefix = '{}/{}'.format(SCREENSHOTS_FOLDER_PREFIX, commit_sha)
    all_files = list_s3_contents(BUCKET_NAME, folder_prefix)
    print('found:')
    print('\n'.join(all_files))
    images = [{
        'src': 'http://{}.s3.eu-central-1.amazonaws.com/{}'.format(BUCKET_NAME, filename),
        'display_name': filename.replace(SCREENSHOTS_FOLDER_PREFIX, '', 1)
    } for filename in all_files]

    html_page = render_template("serve_index.html", **{
        'images': images
    })

    return html_page
