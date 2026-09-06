#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$HOME/lebowski-rag"
APP_USER="$(whoami)"
DOMAIN="${ORACLE_DOMAIN:-}"
DUCKDNS_TOKEN="${DUCKDNS_TOKEN:-}"
DUCKDNS_NAME="${DOMAIN%%.*}"
API_UNIT=/etc/systemd/system/lebowski-api.service
UI_UNIT=/etc/systemd/system/lebowski-ui.service

if [ -z "$DOMAIN" ]; then
  echo "ORACLE_DOMAIN vacío: define el dominio DuckDNS (p. ej. lebowski.duckdns.org)" >&2
  exit 1
fi

sudo apt-get update
sudo apt-get install -y nginx python3-venv python3-pip certbot python3-certbot-nginx curl

if ! command -v ollama >/dev/null 2>&1; then
  curl -fsSL https://ollama.com/install.sh | sh
fi

cd "$APP_DIR"
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -r requirements.txt
bash scripts/setup.sh

if [ ! -f "$APP_DIR/db/chroma.sqlite3" ]; then
  .venv/bin/python ingest.py
fi

sudo tee "$API_UNIT" >/dev/null <<EOF
[Unit]
Description=lebowski-rag API (FastAPI + RAG)
After=network.target ollama.service
Wants=ollama.service

[Service]
User=$APP_USER
WorkingDirectory=$APP_DIR
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo tee "$UI_UNIT" >/dev/null <<EOF
[Unit]
Description=lebowski-rag UI (Streamlit)
After=network.target lebowski-api.service
Wants=lebowski-api.service

[Service]
User=$APP_USER
WorkingDirectory=$APP_DIR
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/.venv/bin/streamlit run app/ui.py --server.address 127.0.0.1 --server.port 8501 --server.headless true
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo tee /etc/nginx/sites-available/lebowski >/dev/null <<EOF
server {
    listen 80;
    server_name $DOMAIN;
    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 3600s;
        proxy_buffering off;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/lebowski /etc/nginx/sites-enabled/lebowski
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx

if [ ! -d "/etc/letsencrypt/live/$DOMAIN" ]; then
  sudo certbot --nginx -d "$DOMAIN" --redirect --non-interactive --agree-tos --register-unsafely-without-email
else
  sudo certbot renew --quiet
fi

if [ -n "$DUCKDNS_TOKEN" ]; then
  (crontab -l 2>/dev/null | grep -v "duckdns.org/update"; echo "*/5 * * * * curl -fsS 'https://www.duckdns.org/update?domains=$DUCKDNS_NAME&token=$DUCKDNS_TOKEN&ip=' >/dev/null 2>&1") | crontab -
  curl -fsS "https://www.duckdns.org/update?domains=$DUCKDNS_NAME&token=$DUCKDNS_TOKEN&ip=" >/dev/null 2>&1 || true
fi

sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

sudo systemctl daemon-reload
sudo systemctl enable --now lebowski-api lebowski-ui
sudo systemctl restart lebowski-api lebowski-ui nginx

echo "Deploy listo: https://$DOMAIN"