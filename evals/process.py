"""Run isolated adapter processes and capture their raw output."""
import os
import signal
import subprocess
import tempfile
import time


def _process(command, cwd, env, prompt, timeout):
    started = time.monotonic()
    with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
        try:
            proc = subprocess.Popen(command, cwd=cwd, env=env, stdin=subprocess.PIPE,
                                    stdout=out, stderr=err, start_new_session=True)
            try:
                proc.communicate(prompt.encode(), timeout=timeout)
                state, code = 'completed', proc.returncode
            except subprocess.TimeoutExpired:
                try: os.killpg(proc.pid, signal.SIGKILL)
                except (ProcessLookupError, AttributeError): proc.kill()
                proc.communicate()
                state, code = 'timeout', None
        except OSError as exc:
            state, code = 'runner-error', None
            err.write(str(exc).encode())
        out.seek(0); err.seek(0)
        return state, code, out.read(), err.read(), round(time.monotonic() - started, 3)
