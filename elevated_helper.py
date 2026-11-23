# elevated_helper.py (2026-11-17, user directive: "all agents run as admin by default,
# same as white. add the elevated helper service as the fallback.")
# Localhost-only command executor that runs ELEVATED (installed as an ONSTART SYSTEM
# task by install_elevated_helper.bat). Lets any non-elevated process (Studio/agent
# terminal tools) run admin-only commands without a UAC prompt.
#
#   POST /run  {"cmd": "...", "shell": true|false}   header X-Elev-Token: <token>
#   GET  /ping                                      -> {ok, elevated, user}
#
# Token lives in elev_token.txt next to this file (or env ELEV_TOKEN).
import json, os, subprocess, ctypes, getpass, threading
from http.server import BaseHTTPRequestHandler, HTTPServer

ROOT = os.path.dirname(os.path.abspath(__file__))
TOKEN_FILE = os.path.join(ROOT, 'elev_token.txt')
LOG = os.path.join(ROOT, 'memory', 'ops', 'elev-helper.log')
PORT = int(os.environ.get('ELEV_HELPER_PORT', '8098'))
TIMEOUT = int(os.environ.get('ELEV_HELPER_TIMEOUT', '120'))

def _token():
    t = os.environ.get('ELEV_TOKEN', '')
    if not t and os.path.exists(TOKEN_FILE):
        t = open(TOKEN_FILE).read().strip()
    return t

def _elevated():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False

def _log(line):
    try:
        with open(LOG, 'a', encoding='utf-8') as f:
            import datetime
            f.write(datetime.datetime.now().isoformat() + ' ' + line + '\n')
    except Exception:
        pass

class H(BaseHTTPRequestHandler):
    def _send(self, code, obj):
        b = json.dumps(obj).encode('utf-8', 'replace')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        if self.path == '/ping':
            self._send(200, {'ok': True, 'elevated': _elevated(), 'user': getpass.getuser()})
        else:
            self._send(404, {'ok': False, 'err': 'not found'})

    def do_POST(self):
        if self.path != '/run':
            return self._send(404, {'ok': False, 'err': 'not found'})
        tok = self.headers.get('X-Elev-Token', '')
        want = _token()
        if not want or tok != want:
            _log('REJECT bad token from %s' % self.client_address[0])
            return self._send(403, {'ok': False, 'err': 'bad token'})
        try:
            n = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(n) or b'{}')
            cmd = body.get('cmd', '')
            shell = bool(body.get('shell', False))
            if not cmd:
                return self._send(400, {'ok': False, 'err': 'empty cmd'})
            _log('RUN %s' % (cmd[:200]))
            p = subprocess.run(cmd if not shell else ['cmd', '/c', cmd],
                               capture_output=True, timeout=TIMEOUT, cwd=ROOT)
            out = p.stdout.decode('utf-8', 'replace')[-20000:]
            err = p.stderr.decode('utf-8', 'replace')[-20000:]
            self._send(200, {'ok': True, 'code': p.returncode, 'out': out, 'err': err,
                             'elevated': _elevated()})
        except subprocess.TimeoutExpired:
            self._send(200, {'ok': True, 'code': 124, 'out': '', 'err': 'timeout %ss' % TIMEOUT})
        except Exception as e:
            self._send(500, {'ok': False, 'err': repr(e)})

    def log_message(self, *a):
        pass

if __name__ == '__main__':
    _log('start pid=%d elevated=%s user=%s' % (os.getpid(), _elevated(), getpass.getuser()))
    HTTPServer(('127.0.0.1', PORT), H).serve_forever()
