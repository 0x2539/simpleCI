import os

from flask import Flask, Response, render_template

app = Flask(__name__)


@app.route('/health-check', methods=['GET'])
def health_check():
    print('health check')
    return Response('', status=200)


@app.route('/<commit_sha>')
def serve_images(commit_sha):
    images = []
    file_server_path = os.environ.get("SERVE_PATH")
    serve_port = os.environ.get("SERVE_PORT")
    screenshots_dir = os.environ.get("SCREENSHOTS_PATH").format(commit_sha)
    print('searching in:', screenshots_dir)

    for root, dirs, files in os.walk(screenshots_dir):
        files.sort()
        print('found files:', files)

        for filename in [os.path.join(root, name) for name in files]:
            if not filename.endswith('.png'):
                continue

            images.append({
                'src': 'http://localhost:{}/{}'.format(serve_port, filename.replace(file_server_path, '', 1)),
                'display_name': filename.replace(file_server_path, '')
            })
    print('found imags:', images)

    html_page = render_template("serve_index.html", **{
        'images': images
    })

    return html_page
