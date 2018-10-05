import json
import os
from flask import Flask, Response, request
from pathlib import Path
from subprocess import Popen, STDOUT
from hmac import HMAC
import hashlib
from tests_queue import get_commit_pr_queue_singleton
from commit_pr_model import CommitPrModel

singleton = get_commit_pr_queue_singleton()
app = Flask(__name__)

@app.route('/keep-latest', methods=['POST'])
def keep_latest():
    pr_dict = {}
    to_remove_commits = []

    for commit_pr in singleton.requests_queue:
        missing_key = commit_pr.pull_request_number not in pr_dict
        is_newer_timestamp = missing_key or commit_pr.timestamp > pr_dict[commit_pr.pull_request_number]

        if missing_key or is_newer_timestamp:
            pr_dict[commit_pr.pull_request_number] = commit_pr.timestamp

    for commit_pr in singleton.requests_queue:
        if pr_dict[commit_pr.pull_request_number] != commit_pr.timestamp:
            to_remove_commits.append(commit_pr)

    for commit_pr in to_remove_commits:
        singleton.remove_obj(commit_pr)

    serialized_commit_pr_list = [commit_pr.serialize() for commit_pr in to_remove_commits]

    return Response(json.dumps({'removed': serialized_commit_pr_list}))

@app.route('/move-commit-to-front', methods=['POST'])
def move_to_front():
    commit = request.get_json()
    to_remove = None

    for commit_pr in singleton.requests_queue:
        if commit['sha'] == commit_pr.commit_sha:
            to_remove = commit_pr

    if not to_remove is None:
        singleton.remove_obj(to_remove)
        singleton.prioritize_obj(to_remove)

        return Response(json.dumps({'message': 'Prioritized commit ' + to_remove.commit_sha}))

    return Response(json.dumps({'message': 'No commit found. No changes were made to the queue'}))


@app.route('/remove-pull-request', methods=['POST'])
def remove_pr():
    pr_list = request.get_json()['pull_requests']
    to_remove_commits = []

    for pr_no in pr_list:
        for commit_pr in singleton.requests_queue:
            if pr_no == commit_pr.pull_request_number:
                to_remove_commits.append(commit_pr)

    for commit_pr in to_remove_commits:
        singleton.remove_obj(commit_pr)

    serialized_commit_pr_list = [commit_pr.serialize() for commit_pr in to_remove_commits]

    return Response(json.dumps({'removed': serialized_commit_pr_list}))

@app.route('/remove-commits', methods=['POST'])
def remove_commits():
    commit_list = request.get_json()['commits']
    to_remove_commits = []

    for commit_sha in commit_list:
        for commit_pr in singleton.requests_queue:
            if commit_sha == commit_pr.commit_sha:
                to_remove_commits.append(commit_pr)

    for commit in to_remove_commits:
        singleton.remove_obj(commit)

    serialized_commit_pr_list  = [commit_pr.serialize() for commit_pr in to_remove_commits]

    return Response(json.dumps({'removed': serialized_commit_pr_list }))

@app.route('/pull-request', methods=['POST'])
def push():
    signature = request.headers.get('X-Hub-Signature')
    if not signature:
        return Response(
            json.dumps({'message': 'missing signature header'}),
            status=403,
            mimetype='application/json',
        )
    secret = os.environ.get('GITHUB_SECRET')
    if not secret:
        return Response(
            json.dumps({'message': 'missing secret environment variable'}),
            status=403,
            mimetype='application/json',
        )
    pull_request = request.get_json()
    payload = json.dumps(pull_request, separators=(',', ':'))

    # if get_signature(secret, payload) != signature:
    #     return Response(
    #         json.dumps({'message': 'bad credentials'}),
    #         status=403,
    #         mimetype='application/json',
    #     )

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
    script_out_file = f"{script_out_folder}/{commit_sha}-debug.txt"
    git_token = os.environ.get('gitToken')
    if not git_token:
        with open(script_out_file, 'w') as outfile:
            outfile.write(
                "git access token is missing, set it as environment variable or pass it as argument ('./run_tests.sh --gitToken=123' or 'export gitToken=123')")
        return Response(json.dumps({'message': "git access token not found"}), status=422, mimetype='application/json')

    if os.environ.get('SYNC') == "true":
        commit_pr = CommitPrModel(commit_sha, pull_request_number, script_out_file)
        singleton.add_commit_pr(commit_pr)

        return Response(
            json.dumps({'message': "Added to queue: " + str(commit_pr.commit_sha)}),
            status=200,
            mimetype='application/json',
        )

    with open(script_out_file, 'w') as outfile:
        pid = Popen(
            f'../run_tests.sh --gitCommit={commit_sha} --gitToken={git_token} --pullRequestNumber={pull_request_number}'.split(),
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


def get_signature(secret, payload):
    return 'sha1=' + HMAC(bytes(secret, 'utf-8'), bytes(payload, 'utf-8'), hashlib.sha1).hexdigest()
