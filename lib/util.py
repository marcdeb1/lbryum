import logging
import os
import re
import sys
import threading
import traceback
from collections import defaultdict
from decimal import Decimal
import socket
import errno
import json
import ssl
import time
import Queue

from i18n import _

log = logging.getLogger("lbryum")

base_units = {'BTC': 8, 'mBTC': 5, 'uBTC': 2}


def normalize_version(v):
    return [int(x) for x in re.sub(r'(\.0+)*$', '', v).split(".")]


class NotEnoughFunds(Exception):
    pass


class InvalidPassword(Exception):
    def __str__(self):
        return _("Incorrect password")


class SilentException(Exception):
    '''An exception that should probably be suppressed from the user'''
    pass


class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        from transaction import Transaction
        if isinstance(obj, Transaction):
            return obj.as_dict()
        return super(MyEncoder, self).default(obj)


class PrintError(object):
    '''A handy base class'''

    def diagnostic_name(self):
        return self.__class__.__name__

    def print_error(self, *msg):
        log.info(" ".join([str(m) for m in list(msg)]))
        print_error("[%s]" % self.diagnostic_name(), *msg)

    def print_msg(self, *msg):
        log.info(" ".join([str(m) for m in list(msg)]))
        print_msg("[%s]" % self.diagnostic_name(), *msg)


class ThreadJob(PrintError):
    """A job that is run periodically from a thread's main loop.  run() is
    called from that thread's context.
    """

    def run(self):
        """Called periodically from the thread"""
        pass


class DebugMem(ThreadJob):
    '''A handy class for debugging GC memory leaks'''

    def __init__(self, classes, interval=30):
        self.next_time = 0
        self.classes = classes
        self.interval = interval

    def mem_stats(self):
        import gc
        self.print_error("Start memscan")
        gc.collect()
        objmap = defaultdict(list)
        for obj in gc.get_objects():
            for class_ in self.classes:
                if isinstance(obj, class_):
                    objmap[class_].append(obj)
        for class_, objs in objmap.items():
            self.print_error("%s: %d" % (class_.__name__, len(objs)))
        self.print_error("Finish memscan")

    def run(self):
        if time.time() > self.next_time:
            self.mem_stats()
            self.next_time = time.time() + self.interval


class DaemonThread(threading.Thread, PrintError):
    """ daemon thread that terminates cleanly """

    def __init__(self):
        threading.Thread.__init__(self)
        self.parent_thread = threading.currentThread()
        self.running = False
        self.running_lock = threading.Lock()
        self.job_lock = threading.Lock()
        self.jobs = []

    def add_jobs(self, jobs):
        with self.job_lock:
            self.jobs.extend(jobs)

    def run_jobs(self):
        # Don't let a throwing job disrupt the thread, future runs of
        # itself, or other jobs.  This is useful protection against
        # malformed or malicious server responses
        with self.job_lock:
            for job in self.jobs:
                try:
                    job.run()
                except:
                    traceback.print_exc(file=sys.stderr)

    def remove_jobs(self, jobs):
        with self.job_lock:
            for job in jobs:
                self.jobs.remove(job)

    def start(self):
        with self.running_lock:
            self.running = True
        return threading.Thread.start(self)

    def is_running(self):
        with self.running_lock:
            return self.running and self.parent_thread.is_alive()

    def stop(self):
        with self.running_lock:
            self.running = False


is_verbose = False


def set_verbosity(b):
    global is_verbose
    is_verbose = b


def print_error(*args):
    if not is_verbose:
        return
    print_stderr(*args)


def print_stderr(*args):
    args = [str(item) for item in args]
    sys.stderr.write(" ".join(args) + "\n")
    sys.stderr.flush()


def print_msg(*args):
    # Stringify args
    args = [str(item) for item in args]
    sys.stdout.write(" ".join(args) + "\n")
    sys.stdout.flush()


def json_decode(x):
    try:
        return json.loads(x, parse_float=Decimal)
    except:
        return x


# decorator that prints execution time
def profiler(func):
    def do_profile(func, args, kw_args):
        n = func.func_name
        t0 = time.time()
        o = func(*args, **kw_args)
        t = time.time() - t0
        print_error("[profiler]", n, "%.4f" % t)
        return o

    return lambda *args, **kw_args: do_profile(func, args, kw_args)


def user_dir():
    if "HOME" in os.environ:
        return os.path.join(os.environ["HOME"], ".lbryum")
    elif "APPDATA" in os.environ:
        return os.path.join(os.environ["APPDATA"], "LBRYum")
    elif "LOCALAPPDATA" in os.environ:
        return os.path.join(os.environ["LOCALAPPDATA"], "LBRYum")
    elif 'ANDROID_DATA' in os.environ:
        try:
            import jnius
            env = jnius.autoclass('android.os.Environment')
            _dir = env.getExternalStorageDirectory().getPath()
            return _dir + '/lbryum/'
        except ImportError:
            pass
        return "/sdcard/lbryum/"
    else:
        # raise Exception("No home directory found in environment variables.")
        return


def format_satoshis(x, is_diff=False, num_zeros=0, decimal_point=8, whitespaces=False):
    from locale import localeconv
    if x is None:
        return 'unknown'
    x = int(x)  # Some callers pass Decimal
    scale_factor = pow(10, decimal_point)
    integer_part = "{:n}".format(int(abs(x) / scale_factor))
    if x < 0:
        integer_part = '-' + integer_part
    elif is_diff:
        integer_part = '+' + integer_part
    dp = localeconv()['decimal_point']
    fract_part = ("{:0" + str(decimal_point) + "}").format(abs(x) % scale_factor)
    fract_part = fract_part.rstrip('0')
    if len(fract_part) < num_zeros:
        fract_part += "0" * (num_zeros - len(fract_part))
    result = integer_part + dp + fract_part
    if whitespaces:
        result += " " * (decimal_point - len(fract_part))
        result = " " * (15 - len(result)) + result
    return result.decode('utf8')


def parse_json(message):
    n = message.find('\n')
    if n == -1:
        return None, message
    try:
        j = json.loads(message[0:n])
    except:
        j = None
    return j, message[n + 1:]


class Timeout(Exception):
    pass


class SocketPipe:
    def __init__(self, socket):
        self.socket = socket
        self.message = ''
        self.set_timeout(0.1)
        self.recv_time = time.time()

    def set_timeout(self, t):
        self.socket.settimeout(t)

    def idle_time(self):
        return time.time() - self.recv_time

    def get(self):
        while True:
            response, self.message = parse_json(self.message)
            if response is not None:
                return response
            try:
                data = self.socket.recv(1024)
            except socket.timeout:
                raise Timeout
            except ssl.SSLError:
                raise Timeout
            except socket.error, err:
                if err.errno == 60:
                    raise Timeout
                elif err.errno in [11, 35, 10035]:
                    # print_error("socket errno %d (resource temporarily unavailable)"% err.errno)
                    time.sleep(0.05)
                    raise Timeout
                else:
                    print_error("pipe: socket error", err)
                    data = ''
            except:
                traceback.print_exc(file=sys.stderr)
                data = ''

            if not data:  # Connection closed remotely
                return None
            self.message += data
            self.recv_time = time.time()

    def send(self, request):
        out = json.dumps(request) + '\n'
        self._send(out)

    def send_all(self, requests):
        out = ''.join(map(lambda x: json.dumps(x) + '\n', requests))
        self._send(out)

    def _send(self, out):
        while out:
            try:
                sent = self.socket.send(out)
                out = out[sent:]
            except ssl.SSLError as e:
                print_error("SSLError:", e)
                time.sleep(0.1)
                continue
            except socket.error as e:
                if e[0] in (errno.EWOULDBLOCK, errno.EAGAIN):
                    print_error("EAGAIN: retrying")
                    time.sleep(0.1)
                    continue
                elif e[0] in ['timed out', 'The write operation timed out']:
                    print_error("socket timeout, retry")
                    time.sleep(0.1)
                    continue
                else:
                    traceback.print_exc(file=sys.stdout)
                    raise e


class QueuePipe:
    def __init__(self, send_queue=None, get_queue=None):
        self.send_queue = send_queue if send_queue else Queue.Queue()
        self.get_queue = get_queue if get_queue else Queue.Queue()
        self.set_timeout(0.1)

    def get(self):
        try:
            return self.get_queue.get(timeout=self.timeout)
        except Queue.Empty:
            raise Timeout

    def get_all(self):
        responses = []
        while True:
            try:
                r = self.get_queue.get_nowait()
                responses.append(r)
            except Queue.Empty:
                break
        return responses

    def set_timeout(self, t):
        self.timeout = t

    def send(self, request):
        self.send_queue.put(request)

    def send_all(self, requests):
        for request in requests:
            self.send(request)


class StoreDict(dict):
    def __init__(self, config, name):
        self.config = config
        self.path = os.path.join(self.config.path, name)
        self.load()

    def load(self):
        try:
            with open(self.path, 'r') as f:
                self.update(json.loads(f.read()))
        except:
            pass

    def save(self):
        with open(self.path, 'w') as f:
            s = json.dumps(self, indent=4, sort_keys=True)
            r = f.write(s)

    def __setitem__(self, key, value):
        dict.__setitem__(self, key, value)
        self.save()

    def pop(self, key):
        if key in self.keys():
            dict.pop(self, key)
            self.save()
