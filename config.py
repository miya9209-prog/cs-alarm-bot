name: Misharp CS Board Alert

on:
  schedule:
    # 10분마다 실행. GitHub 상황에 따라 몇 분 지연될 수 있습니다.
    - cron: "*/10 * * * *"
  workflow_dispatch:

jobs:
  check-cs-board:
    runs-on: ubuntu-latest
    permissions:
      contents: write

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Check new CS posts and send alert
        env:
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
          BOARD_URLS: ${{ secrets.BOARD_URLS }}
          CHECK_LIMIT: ${{ secrets.CHECK_LIMIT }}
          STATE_FILE: data/notified_posts.json
        run: python -m src.check_new_posts

      - name: Save notification state
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add data/notified_posts.json || true
          git diff --cached --quiet || git commit -m "Update notified CS posts"
          git push || true
