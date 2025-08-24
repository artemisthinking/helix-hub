# 🏔️ Helix Hub – Cloud Quick Start & DevOps Karate Kid Guide

## 🚀 What You’ll Learn
- How to deploy a full cloud stack on DigitalOcean for $5/month
- SSH key setup, VS Code Remote, and Portainer for pro-grade management
- Fast file transfer, service discovery, and health checks
- Real-world tips for daily dev workflow

---

## 1️⃣ SSH Key Setup & VS Code Remote

```bash
# Generate a new SSH key (if needed)
ssh-keygen -t ed25519 -C "your_email@example.com"

# Add your public key to the DO server
ssh-copy-id -i ~/.ssh/id_ed25519.pub root@206.189.30.236

# (Optional) Check your key fingerprint
ssh-keygen -lf ~/.ssh/id_ed25519

# Add to ~/.ssh/config for easy access
cat <<EOF >> ~/.ssh/config
Host helix-do
    HostName 206.189.30.236
    User root
    IdentityFile ~/.ssh/id_ed25519
EOF

# Connect with VS Code Remote SSH (select 'helix-do')
```

---

## 2️⃣ Copy Files & Folders (SCP)

```bash
# Copy a script
scp helix-service-discovery.sh helix-do:/root/helix-hub/

# Copy a whole folder
scp -r helix-core helix-do:/root/helix-hub/
```

---

## 3️⃣ Deploy Services (Docker Compose)

```bash
# Start only the low-resource stack
docker compose up -d traefik vault filebrowser helix-core

# Stop all containers
docker compose down
```

---

## 4️⃣ Service Discovery & Health Checks

```bash
# Run your dynamic service discovery script
./helix-service-discovery.sh

# See live status, clickable public URLs, and tips for each service
```

---

## 5️⃣ Portainer – Cloud Management UI

- Access Portainer at: `https://206.189.30.236:9443/`
- Manage containers, stacks, images, volumes, and logs
- Monitor resource usage and troubleshoot with a few clicks

---

## 6️⃣ Pro Tips & Daily Dev Workflow

- Use VS Code Remote SSH for direct cloud coding and terminal access
- Use SCP for fast file/folder transfer
- Use Portainer for web-based management and monitoring
- Use your service discovery script for instant CLI status
- Always check public URLs for your services (HTTP/HTTPS)
- Tune health checks to validate endpoints and service status

---

## 🥋 DevOps Karate Kid Wisdom

- Practice SSH, SCP, and Docker daily—become a cloud ninja!
- Keep your README and scripts up to date for instant onboarding
- Use emoji and clear output for fun, readable logs
- Test, monitor, and iterate—cloud is your dojo!

---

**Ready to deploy, monitor, and manage like a pro?  
You’ve got all the tools—just keep practicing! 🐣🥋🚀**
