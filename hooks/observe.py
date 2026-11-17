"""Bounded allowlisted hook history; never read source, prompts or transcripts."""
import json
import fcntl
import os
from pathlib import Path
import re
import stat
import time

LIMIT = 1024 * 1024
EVENTS = ('SessionStart', 'UserPromptSubmit', 'SubagentStart')


def observe(payload, data_path, *, context_sha256=None):
    if not isinstance(payload, dict) or payload.get('hook_event_name') not in EVENTS:
        raise ValueError('Unsupported event')
    session = payload.get('session_id')
    if not isinstance(session, str) or not re.fullmatch(r'[\w.:/-]{1,256}', session, re.ASCII):
        raise ValueError('Invalid session id')
    if context_sha256 is not None and not re.fullmatch(r'[a-f0-9]{64}', context_sha256):
        raise ValueError('Invalid context hash')
    row = {'schema': 1, 'source': 'observed_hook', 'event': payload['hook_event_name'],
           'session_id': session, 'time': time.time(), 'status': 'OBSERVED'}
    if context_sha256 is not None:
        row.update(context_sha256=context_sha256, context_emitted=True)
    data_path = Path(data_path)
    if not data_path.is_absolute():
        raise ValueError('Absolute host data path required')
    data_path.mkdir(mode=0o700, parents=True, exist_ok=True)
    directory = os.open(data_path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        fd = os.open('events.jsonl', os.O_WRONLY | os.O_APPEND | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK,
                     0o600, dir_fd=directory)
        try:
            # Do not wait behind another handler: losing a metadata record must
            # not delay context delivery. The lock bounds check+append together.
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            info = os.fstat(fd)
            line = (json.dumps(row, separators=(',', ':')) + '\n').encode()
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_size + len(line) > LIMIT:
                raise ValueError('Unsafe or full event log')
            os.fchmod(fd, 0o600)
            if os.write(fd, line) != len(line):
                raise OSError('Incomplete event log write')
        finally:
            os.close(fd)
    finally:
        os.close(directory)
    return row
