import signal
from collections import deque
from threading import Thread, Semaphore
from subprocess import Popen, STDOUT
import subprocess
import os

class __CommitPrQueueThread(object):
    def __init__(self):
        self.__exit = False

        # deque is more efficient than a queue, O(1) for both append and pop
        # (https://wiki.python.org/moin/TimeComplexity)
        self.requests_queue = self.__get_pending_requests_queue()
        # set initial value to length of queue so we process it all
        self.__stop_event = Semaphore(0)

    def prioritize_obj(self, commit_pr):
        self.requests_queue.append(commit_pr)
        self.__stop_event.release()

    def remove_obj(self, commit_pr):
        self.requests_queue.remove(commit_pr)
        self.__stop_event.acquire()

    def __serve_forever(self):
        while not self.__exit:
            # wait until resume is called
            self.__stop_event.acquire()
            self.__run()

    def add_commit_pr(self, commit_pr):
        queue_obj = commit_pr
        self.requests_queue.appendleft(queue_obj)
        self.__stop_event.release()

        return len(self.requests_queue)

    def __run(self) -> None:
        commit_pr_model = self.requests_queue.pop()
        print('Started running for commit: ' + commit_pr_model.commit_sha)

        git_token = os.environ.get('gitToken')
        if not git_token:
            print("Git token missing for commit: " + commit_pr_model.commit_sha)

            with open(commit_pr_model.script_out_file, 'w') as outfile:
                outfile.write(
                    "git access token is missing, set it as environment variable or pass it as argument ('./run_tests.sh --gitToken=123' or 'export gitToken=123')")

        with open(commit_pr_model.script_out_file, 'w') as outfile:
            p = Popen(
                f'../run_tests.sh --gitCommit={commit_pr_model.commit_sha} --gitToken={git_token} --pullRequestNumber={commit_pr_model.pull_request_number}'.split(),
                stdout=outfile,
                stderr=STDOUT,
            )
            p.communicate()

        print('Finished running for commit: ' + commit_pr_model.commit_sha)

    def __start_job_thread(self):
        """
        If you are planing on doing sleeps, its absolutely imperative that you use the Event().wait(seconds) to do the
        sleep. If you leverage the event to sleep, if someone tells you to stop while "sleeping" it will wake up. If
        you use time.sleep() your thread will only stop after it wakes up.
        """
        print('Started job thread')

        Thread(target=self.__serve_forever, args=()).start()
        signal.signal(signal.SIGINT, lambda signal, frame: self.__signal_handler(signal, frame))

    def __signal_handler(self, signal, frame):
        print('Received signal')

        self.__exit = True
        self.__stop_event.release()
        raise KeyboardInterrupt  # will be catched by flask to kill reservation_system_app

    def start(self):
        self.__start_job_thread()
        return self

    def __get_pending_requests_queue(self):
        return deque()

    def __run_command(self, command):
        source_path = os.path.abspath(os.path.curdir)
        print('running command: {}\n'.format(command))
        return_code = subprocess.call(command, shell=True, cwd=source_path)
        if return_code != 0:
            print('failed command: "{}"'.format(command))
            # sys.exit(-1)
            return False
        return True

__commit_pr_queue_thread_singleton = None

def get_commit_pr_queue_singleton():
    global __commit_pr_queue_thread_singleton
    if not __commit_pr_queue_thread_singleton:
        __commit_pr_queue_thread_singleton = __CommitPrQueueThread().start()
    return __commit_pr_queue_thread_singleton
