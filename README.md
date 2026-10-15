# Workday Job Notifier

Automatically monitor multiple Workday career sites for new job postings, use local AI (Ollama) to semantically match jobs against your filters, and get instant Telegram notifications.

## Features

- Direct HTTP calls to Workday’s hidden JSON API (no scraping)
- Full pagination, fetches all jobs
- Local AI matching with Ollama (Gemma 3 4B) – semantic, not keyword‑based
- Telegram notifications (primary) with optional email
- SQLite deduplication – you’ll never be notified twice for the same job
- Runs continuously in the background

## Prerequisites

- **Python 3.11+**
- **Ollama** – download from [ollama.com](https://ollama.com)
- A **Telegram Bot** – get it from [@BotFather](https://t.me/BotFather)

## Setup

1. **Clone or unzip** the project and `cd` into the folder.

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt