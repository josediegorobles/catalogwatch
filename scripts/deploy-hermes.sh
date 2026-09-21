#!/usr/bin/env bash
# Install CatalogWatch on a Debian/Ubuntu server and schedule the daily fleet crawl.
#
# Run it ON the server:
#   bash deploy-hermes.sh [stores.txt]
# Or from your machine once SSH access works:
#   scp scripts/deploy-hermes.sh stores.txt hermes@169.58.71.10:~/
#   ssh hermes@169.58.71.10 'bash ~/deploy-hermes.sh ~/stores.txt'
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/josediegorobles/catalogwatch.git}"
TARGET="${TARGET:-$HOME/catalogwatch}"
STORES_SRC="${1:-}"
CRON_HOUR="${CRON_HOUR:-07}"
KEEP_BACKUPS="${KEEP_BACKUPS:-7}"

log() { printf '\n== %s\n' "$*"; }

log "Dependencies"
if ! command -v python3 >/dev/null || ! command -v git >/dev/null; then
  sudo apt-get update -qq
  sudo apt-get install -y -qq python3 python3-venv git sqlite3
fi
python3 --version

log "Code in $TARGET"
if [ -d "$TARGET/.git" ]; then
  git -C "$TARGET" pull --ff-only
else
  git clone --depth 1 "$REPO_URL" "$TARGET"
fi

log "Virtualenv and install"
cd "$TARGET"
python3 -m venv .venv
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q .

if [ -n "$STORES_SRC" ]; then
  log "Stores list from $STORES_SRC"
  cp "$STORES_SRC" "$TARGET/stores.txt"
fi
if [ ! -s "$TARGET/stores.txt" ]; then
  printf '# one store URL per line\nhttps://www.allbirds.com\n' > "$TARGET/stores.txt"
  echo "WARNING: no stores file provided, wrote a one-store placeholder"
fi

log "Backup helper"
cat > "$TARGET/backup-history.sh" <<'BACKUP'
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p backups
sqlite3 history.sqlite ".backup 'backups/history-$(date +%F).sqlite'"
ls -1t backups/history-*.sqlite | tail -n +8 | xargs -r rm --
echo "backups: $(ls -1 backups | wc -l) file(s)"
BACKUP
chmod +x "$TARGET/backup-history.sh"

log "systemd units (daily at ${CRON_HOUR}:00)"
sudo tee /etc/systemd/system/catalogwatch-fleet.service >/dev/null <<UNIT
[Unit]
Description=CatalogWatch fleet crawl
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=$USER
WorkingDirectory=$TARGET
ExecStart=/bin/bash -lc 'cd $TARGET && .venv/bin/catalogwatch fleet --stores stores.txt --db history.sqlite --reports reports --max-pages 1 --quiet'
ExecStartPost=/bin/bash -lc '$TARGET/backup-history.sh'
UNIT

sudo tee /etc/systemd/system/catalogwatch-fleet.timer >/dev/null <<UNIT
[Unit]
Description=Run the CatalogWatch fleet crawl every day

[Timer]
OnCalendar=*-*-* ${CRON_HOUR}:00:00
Persistent=true
RandomizedDelaySec=600

[Install]
WantedBy=timers.target
UNIT

sudo systemctl daemon-reload
sudo systemctl enable --now catalogwatch-fleet.timer

log "First run"
.venv/bin/catalogwatch fleet --stores stores.txt --db history.sqlite --reports reports --max-pages 1 || true

log "State"
systemctl list-timers catalogwatch-fleet.timer --no-pager | head -3
.venv/bin/python - <<'PY'
from pathlib import Path
from catalogwatch.history import connect, store_stats
path = Path("history.sqlite")
print(f"history.sqlite: {path.stat().st_size / 1_048_576:.1f} MB" if path.exists() else "history.sqlite: not created yet")
if path.exists():
    for row in store_stats(connect(path)):
        print(f"  {row['store']}  {row['skus']} SKUs  {row['changes']} changes")
PY

log "Done. Off-site copies are still your call: the daily backup stays on this server."
