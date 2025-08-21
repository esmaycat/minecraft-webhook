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

PATTERNS = (
    re.compile(r'\[\d\d:\d\d:\d\d\] \[Server thread\/INFO\]: ([^\s]+ left the game)'),
    re.compile(r'\[\d\d:\d\d:\d\d\] \[Server thread\/INFO\]: ([^\s]+ joined the game)'),
    re.compile(r'\[\d\d:\d\d:\d\d\] \[Server thread\/INFO\]: (<[^\s]+> .+)'),
)

if len(sys.argv) != 2:
    print('Invalid argument.', file=sys.stderr)
    sys.exit(1)
else:
    _fp = Path(sys.argv[1])
    try:
        fp = _fp.resolve(strict=True)
    except OSError:
        print(f"'{_fp}' does not exist.", file=sys.stderr)
        sys.exit(1)


def send_message(content):
    resp = requests.post(webhook, json={'content': content})
    if 200 <= resp.status_code <= 300:
        print(f"Sent message '{content}' successfully.")
    else:
        print(f'Failed to send message with code {resp.status_code}.')


class EventHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if isinstance(event.src_path, bytes):
            _src_path = event.src_path.decode()
        else:
            _src_path = event.src_path
        src_path = Path(_src_path).resolve()

        if src_path != fp:
            return

        with open(src_path) as f:
            last_line = None
            for line in f:
                last_line = line

        if last_line:
            for pat in PATTERNS:
                m = re.search(pat, last_line)
                if m:
                    send_message(m.group(1))


def main():
    print('Hello from minecraft-webhook!')

    observer = Observer()
    observer.schedule(EventHandler(), str(fp.parent))
    observer.start()

    try:
        while observer.is_alive():
            observer.join(1)
    finally:
        observer.stop()
        observer.join()


if __name__ == '__main__':
    main()
