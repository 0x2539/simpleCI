import datetime

class CommitPrModel:
    def __init__(self, commit_sha, pull_request_number, script_out_file):

        self.commit_sha = commit_sha
        self.pull_request_number = pull_request_number
        self.timestamp = datetime.datetime.now()
        self.script_out_file = script_out_file

    def serialize(self):
        return {
            'commit_sha': self.commit_sha,
            'pull_request_number': self.pull_request_number,
            'timestamp': str(self.timestamp),
        }