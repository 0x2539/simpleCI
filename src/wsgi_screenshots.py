import os

from flask import Flask, Response, render_template

app = Flask(__name__)


@app.route('/health-check', methods=['GET'])
def health_check():
    return Response('', status=200)


@app.route('/<commit_sha>')
def serve_images(commit_sha):
    images = []
    file_server_path = os.environ.get("FILE_SERVER_PATH")
    screenshots_dir = os.environ.get("SCREENSHOTS_PATH").format(commit_sha)
    print('searching in:', screenshots_dir)

    for root, dirs, files in os.walk(screenshots_dir):
        files.sort()
        print('found files:', files)

        for filename in [os.path.join(root, name) for name in files]:
            if not filename.endswith('.png'):
                continue

            images.append({
                'src': filename.replace(file_server_path, ''),
                'display_name': filename.replace(screenshots_dir, '')
            })
        print('found imags:', images)

    html_page = render_template("serve_index.html", **{
        'images': images
    })

    return html_page
