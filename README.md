## minecraft-webhook

A service to forward server messages to a Discord webhook.

### Instructions

1. Clone the repository.
2. [Install uv](https://docs.astral.sh/uv/getting-started/installation/) and run `uv sync` or, if you want to use pip, run `pip install requests watchdog` (preferably in a virtual environment).
3. Create a webhook in the channel you want the messages to be sent to and copy its "Webhook URL".
4. Create a file named config.py in the root directory and paste in the webhook URL like so: `webhook = '...'`.
5. Run the program with `uv run main.py /path/to/your/server/logs/latest.log`. If you're not using uv then run `python3 main.py` (or whatever Python is called on your system).

The server log file can be found in the `logs` directory from the root of your minecraft server.