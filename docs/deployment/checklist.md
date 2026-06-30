# New Server Deployment Checklist

## 1. Server Provisioning
- [ ] Create VPS (Contabo Cloud VPS 20 minimum — 12GB RAM)
- [ ] Note the public IP address
- [ ] SSH in with root password: `ssh root@<ip>`

## 2. Server Dependencies
- [ ] Install Docker + Docker Compose:
  ```bash
  curl -fsSL https://get.docker.com | sh
  ```
- [ ] Clone the repo:
  ```bash
  git clone https://github.com/Pablito2442/TFG-B2B.git /root/TFG-B2B
  cd /root/TFG-B2B
  ```
- [ ] Copy and edit `.env`:
  ```bash
  cp .env.example .env
  nano .env   # set JWT_SECRET_KEY and PUBLIC_URL
  ```

## 3. SSH Key (for GitHub Actions CD)
- [ ] Add your deploy public key to the server:
  ```bash
  mkdir -p ~/.ssh && chmod 700 ~/.ssh
  echo "<your-public-key>" >> ~/.ssh/authorized_keys
  chmod 600 ~/.ssh/authorized_keys
  ```
- [ ] Test passwordless login from local: `ssh root@<ip>`

## 4. GitHub Secrets (repo → Settings → Secrets → Actions)
- [ ] `HETZNER_HOST` → new server IP
- [ ] `HETZNER_SSH_KEY` → private key (if changed)
- [ ] `HETZNER_USER` → `root` (usually unchanged)
- [ ] `SONAR_TOKEN` → unchanged (SonarCloud)

## 5. DNS
- [ ] Update DuckDNS (or domain provider) A record → new server IP
- [ ] Verify propagation: `nslookup b2b-graph-intelligence.duckdns.org`

## 6. Config Files (only if domain changes)
- [ ] `nginx/nginx.conf` → update `server_name` and cert paths
- [ ] `.env` → update `PUBLIC_URL=https://your-new-domain.com`
- [ ] Commit + push changes so CD picks them up

## 7. SSL Certificate
```bash
docker compose stop nginx
apt-get install -y certbot
certbot certonly --standalone \
  -d b2b-graph-intelligence.duckdns.org \
  --config-dir /root/TFG-B2B/certbot/certs \
  --work-dir /tmp/certbot \
  --logs-dir /tmp/certbot-logs \
  --email pmatego@gmail.com \
  --agree-tos \
  --non-interactive
```

## 8. Start the App
```bash
docker compose up -d
```

## 9. Verify
- [ ] `docker compose ps` → all containers healthy
- [ ] `docker compose logs nginx --tail=20` → no cert errors
- [ ] Open `https://b2b-graph-intelligence.duckdns.org` in browser
- [ ] Run a test pipeline from the UI

## 10. Certificate Auto-renewal
```bash
# Add to crontab so cert renews automatically every 60 days
crontab -e
# Add this line:
0 3 1 * * docker compose -f /root/TFG-B2B/docker-compose.yml stop nginx && certbot renew --config-dir /root/TFG-B2B/certbot/certs --work-dir /tmp/certbot --logs-dir /tmp/certbot-logs && docker compose -f /root/TFG-B2B/docker-compose.yml up -d nginx
```

---

> **Note:** The only things that change between servers are steps 3, 4, 5, 6, and 7 — everything else is identical.