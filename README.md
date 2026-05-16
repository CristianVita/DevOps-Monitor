# 🖥️ DevOps Monitor

A lightweight site monitoring tool with real-time Telegram alerts.

## What it does

- Monitors any website for availability
- Sends instant Telegram alerts when a site goes down
- Distinguishes between DOWN and BLOCKED (403) status
- Runs continuously in the background with two parallel threads
- Fully controlled via Telegram commands — no code editing needed

## Telegram Commands

| Command | Description |
|--------|-------------|
| `/add https://site.com` | Add a site to monitor |
| `/remove https://site.com` | Remove a site |
| `/list` | Show all monitored sites |
| `/status` | Check all sites right now |
| `/help` | Show available commands |

## Setup

1. Clone the repository -> git clone https://github.com/CristianVita/DevOps-Monitor.git
2. Install dependencies -> pip install python-dotenv
3. Create your `.env` file -> cp .env.example .env; Then edit `.env` with your Telegram token and chat ID.
4. Run -> python monitor.py


## How to get your Telegram credentials

1. Open Telegram and search for **@BotFather**
2. Send `/newbot` and follow the steps
3. Copy the token you receive
4. Send any message to your bot, then visit:
   `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
5. Copy the `id` value from the `chat` field

## Tech Stack

- Python 3.13+
- `urllib` — HTTP requests
- `threading` — parallel monitoring and command listening
- `python-dotenv` — environment variable management
- Telegram Bot API