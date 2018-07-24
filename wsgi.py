import json
import os
from flask import Flask, Response, request
from pathlib import Path
from subprocess import Popen, STDOUT
from hmac import HMAC
import hashlib

app = Flask(__name__)


@app.route('/pull-request', methods=['POST'])
def push():
    signature = request.headers.get('X-Hub-Signature')
    if not signature:
        return Response(
            json.dumps({'message': 'missing signature header'}),
            status=403,
            mimetype='application/json',
        )
    pull_request = request.get_json()
    if get_signature(json.dumps(pull_request, separators=(',', ':'))) != signature:
        return Response(
            json.dumps({'message': 'bad credentials'}),
            status=403,
            mimetype='application/json',
        )

    if not pull_request.get('action'):
        return Response(
            json.dumps({'message': "skipping tests, didn't find any action"}),
            status=200,
            mimetype='application/json',
        )
    run_tests = False
    if pull_request['action'] == 'opened':
        run_tests = True
    elif pull_request['action'] == 'synchronize' and pull_request['before'] != pull_request['after']:
        run_tests = True

    if not run_tests:
        return Response(
            json.dumps({'message': "skipping tests, didn't find any new commits"}),
            status=200,
            mimetype='application/json',
        )

    commit_sha = pull_request['pull_request']['head']['sha']
    pull_request_number = pull_request['pull_request']['number']

    script_out_folder = f"{str(Path.home())}/buildMessages"
    os.makedirs(script_out_folder, exist_ok=True)
    script_out_file = f"{script_out_folder}/{commit_sha}.txt"
    git_token = os.environ.get('gitToken')
    if not git_token:
        with open(script_out_file, 'w') as outfile:
            outfile.write(
                "git access token is missing, set it as environment variable or pass it as argument ('./run_tests.sh --gitToken=123' or 'export gitToken=123')")
        return Response(json.dumps({'message': "git access token not found"}), status=422, mimetype='application/json')

    with open(script_out_file, 'w') as outfile:
        pid = Popen(
            f'./run_tests.sh --gitCommit={commit_sha} --gitToken={git_token} --pullRequestNumber={pull_request_number}'.split(),
            stdout=outfile,
            stderr=STDOUT,
        ).pid

    return Response(
        json.dumps({'message': "started to run tests", 'pid': pid}),
        status=200,
        mimetype='application/json',
    )


@app.route('/health-check', methods=['GET'])
def health_check():
    return Response('', status=200)


def get_signature(payload):
    return 'sha1=' + HMAC(bytes(os.environ.get('GITHUB_SECRET'), 'utf-8'), bytes(payload, 'utf-8'), hashlib.sha1).hexdigest()
