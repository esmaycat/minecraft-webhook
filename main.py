import re
import sys
from pathlib import Path

import requests
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

try:
    from config import webhook
except ImportError:
    print(
        "Please create a 'config.py' file and follow the instructions in this project's README.",
        file=sys.stderr,
    )
    sys.exit(1)

PATTERNS = tuple(
    map(
        re.compile,
        (
            r'\[\d\d:\d\d:\d\d\] \[Server thread\/INFO\]: ([^\s]+ left the game)',
            r'\[\d\d:\d\d:\d\d\] \[Server thread\/INFO\]: ([^\s]+ joined the game)',
            r'\[\d\d:\d\d:\d\d\] \[Server thread\/INFO\]: (<[^\s]+> .+)',
            r'\[\d\d:\d\d:\d\d\] \[Server thread\/INFO\]: ([^\s]+ has made the advancement \[.+\])',
            r'\[\d\d:\d\d:\d\d\] \[Server thread\/INFO\]: ([^\s]+ has reached the goal \[.+\])',
            r'\[\d\d:\d\d:\d\d\] \[Server thread\/INFO\]: ([^\s]+ has completed the challenge \[.+\])',
        ),
    )
)


def send_message(content: str) -> None:
    try:
        resp = requests.post(webhook, json={'content': content})
    except Exception:
        print(
            'Failed to make request to webhook. Make sure that the URL is correct.',
            file=sys.stderr,
        )
        raise
    if 200 <= resp.status_code <= 300:
        print(f"Sent message '{content}' successfully.", file=sys.stderr)
    else:
        print(f'Failed to send message with code {resp.status_code}.', file=sys.stderr)
        print('Server response reproduced below.', file=sys.stderr)
        print(resp.text, file=sys.stderr)


class EventHandler(FileSystemEventHandler):
    def __init__(self, target: Path):
        super().__init__()

        self.target = target
        self._last_size = target.stat().st_size

    def on_modified(self, event):
        if isinstance(event.src_path, bytes):
            _src_path = event.src_path.decode()
        else:
            _src_path = event.src_path
        src_path = Path(_src_path).resolve()

        if src_path != self.target:
            return

        size = src_path.stat().st_size
        # File size has not changed; don't bother to read
        if size == self._last_size:
            return
        # Logs files are archived if we restart the server
        elif size < self._last_size:
            self._last_size = size
            return

        with open(src_path) as f:
            f.seek(self._last_size)
            lines = f.read().splitlines()
            self._last_size = f.tell()

        for line in lines:
            for pat in PATTERNS:
                m = re.search(pat, line)
                if m:
                    send_message(m.group(1))


def main():
    print('Hello from minecraft-webhook!')

    if len(sys.argv) != 2:
        print('Invalid argument.', file=sys.stderr)
        sys.exit(1)

    _fp = Path(sys.argv[1])
    try:
        fp = _fp.resolve(strict=True)
    except OSError:
        print(f"'{_fp}' does not exist.", file=sys.stderr)
        sys.exit(1)

    observer = Observer()
    observer.schedule(EventHandler(fp), str(fp.parent))
    observer.start()

    try:
        while observer.is_alive():
            observer.join(1)
    except KeyboardInterrupt:
        print(file=sys.stderr)
    finally:
        observer.stop()
        observer.join()


if __name__ == '__main__':
    main()
