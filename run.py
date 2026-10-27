"""One command to run MoveWell locally.

    python run.py              set up (first time), build the app, open it in your browser
    python run.py notebook     run the analysis notebook top to bottom and check it reproduces (ALL MATCH)
    python run.py all          both: run the notebook, then build and open the app
    python run.py build        only rebuild the app (app/ and public/index.html)

The first run creates a virtual environment in .venv and installs requirements.txt;
later runs reuse it (it reinstalls only if requirements.txt changes). Works on
Windows, macOS and Linux. Press Ctrl+C to stop the local web server.
"""
import hashlib, os, socket, subprocess, sys, threading, time, venv, webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV = ROOT / '.venv'
PY = VENV / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
REQ = ROOT / 'requirements.txt'
NOTEBOOK = ROOT / 'notebooks' / 'MoveWell_Analysis.ipynb'


def step(msg):
    print(f'\n== {msg}', flush=True)


def ensure_env():
    """Create .venv and install requirements if needed, then re-run this script inside it."""
    if not PY.exists():
        step('Creating virtual environment (.venv), first run only')
        venv.EnvBuilder(with_pip=True).create(VENV)
    stamp, want = VENV / '.requirements.sha1', hashlib.sha1(REQ.read_bytes()).hexdigest()
    if not stamp.exists() or stamp.read_text() != want:
        step('Installing requirements')
        subprocess.check_call([str(PY), '-m', 'pip', 'install', '--disable-pip-version-check', '-q', '-r', str(REQ)])
        stamp.write_text(want)
    if Path(sys.executable).resolve() != PY.resolve():
        sys.exit(subprocess.call([str(PY), str(ROOT / 'run.py'), *sys.argv[1:]]))


def build():
    step('Building the app')
    subprocess.check_call([sys.executable, str(ROOT / 'app' / 'build.py')])


def run_notebook():
    import nbformat
    from nbclient import NotebookClient
    step(f'Running {NOTEBOOK.relative_to(ROOT)} (about a minute)')
    t0 = time.time()
    nb = nbformat.read(NOTEBOOK, as_version=4)
    from nbclient.exceptions import CellExecutionError
    try:
        NotebookClient(nb, timeout=1800, kernel_name='python3', resources={'metadata': {'path': str(NOTEBOOK.parent)}}).execute()
    except CellExecutionError as e:
        lines = [l for l in str(e).splitlines() if l.strip()]
        print('a cell failed:', lines[-1] if lines else e); return False
    nbformat.write(nb, NOTEBOOK)
    texts = [o.get('text', '') for c in nb.cells if c.cell_type == 'code' for o in c.get('outputs', []) if o.get('output_type') == 'stream']
    last = texts[-1].strip() if texts else ''
    print(f'finished in {time.time() - t0:.0f} s, results saved into the notebook')
    print(f'app check: {last}')
    return last == 'ALL MATCH'


def free_port(start=8000):
    for port in range(start, start + 50):
        with socket.socket() as s:
            if s.connect_ex(('127.0.0.1', port)) != 0: return port
    raise RuntimeError('no free port between 8000 and 8049')


def serve():
    import http.server, functools
    port = free_port(); url = f'http://localhost:{port}/'
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass                        # keep the terminal quiet
    handler = functools.partial(Quiet, directory=str(ROOT / 'public'))
    httpd = http.server.ThreadingHTTPServer(('127.0.0.1', port), handler)
    step(f'MoveWell is running at {url}  (Ctrl+C to stop)')
    threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try: httpd.serve_forever()
    except KeyboardInterrupt: print('\nstopped')


if __name__ == '__main__':
    cmd = (sys.argv[1] if len(sys.argv) > 1 else 'app').lower()
    if cmd not in ('app', 'notebook', 'all', 'build'):
        print(__doc__); sys.exit(1)
    ensure_env()
    ok = True
    if cmd in ('notebook', 'all'): ok = run_notebook()
    if cmd in ('app', 'all', 'build'): build()
    if cmd in ('app', 'all'): serve()
    sys.exit(0 if ok else 1)
