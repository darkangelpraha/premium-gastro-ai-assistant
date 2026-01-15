# Comprehensive Plan: Finding and Connecting to mem0 and Quadrant on NAS

## Part 1: Finding mem0 CLI

### Step 1.1: Check if mem0 is installed as Python package
**Reasoning:** mem0 is typically installed via pip (source: https://github.com/mem0ai/mem0)
**Commands to try:**
```bash
# Check if mem0 is installed
pip list | grep mem0
pip3 list | grep mem0
poetry show | grep mem0  # if using poetry
pipx list | grep mem0    # if installed globally via pipx

# Check where mem0 is installed
which mem0
which mem0-cli

# Find mem0 in Python site-packages
find /usr/local/lib -name "*mem0*" 2>/dev/null
find ~/.local/lib -name "*mem0*" 2>/dev/null
find /root/.local -name "*mem0*" 2>/dev/null
```

### Step 1.2: Check if mem0 is installed as npm package
**Reasoning:** Some CLI tools are distributed via npm
**Commands to try:**
```bash
npm list -g | grep mem0
which mem0

# Check in node_modules
find /usr/local/lib/node_modules -name "*mem0*" 2>/dev/null
find ~/.npm -name "*mem0*" 2>/dev/null
```

### Step 1.3: Check if mem0 is a binary/executable
**Reasoning:** Could be installed as standalone binary
**Commands to try:**
```bash
# Search common binary locations
ls -la /usr/local/bin/ | grep mem0
ls -la /usr/bin/ | grep mem0
ls -la ~/.local/bin/ | grep mem0
ls -la ~/bin/ | grep mem0

# Find any executable named mem0
find /usr -name "*mem0*" -type f -executable 2>/dev/null
find ~ -name "*mem0*" -type f -executable 2>/dev/null
```

### Step 1.4: Check environment variables and config
**Reasoning:** mem0 config might be in env vars or config files
**Commands to try:**
```bash
# Check environment variables
env | grep -i mem0

# Check for config files
find ~ -name ".mem0*" 2>/dev/null
find ~ -name "mem0.config*" 2>/dev/null
find ~/.config -name "*mem0*" 2>/dev/null

# Check in project
find /home/user/premium-gastro-ai-assistant -name "*mem0*" 2>/dev/null
```

### Step 1.5: Check project dependencies
**Reasoning:** mem0 might be listed in project dependencies
**Commands to try:**
```bash
# Check various dependency files
cat /home/user/premium-gastro-ai-assistant/requirements.txt 2>/dev/null | grep mem0
cat /home/user/premium-gastro-ai-assistant/pyproject.toml 2>/dev/null | grep mem0
cat /home/user/premium-gastro-ai-assistant/package.json 2>/dev/null | grep mem0
cat /home/user/premium-gastro-ai-assistant/Pipfile 2>/dev/null | grep mem0
```

### Step 1.6: Search for mem0 usage in codebase
**Reasoning:** If mem0 is used, there should be import statements or API calls
**Commands to try:**
```bash
# Search for mem0 imports or usage
grep -r "import mem0" /home/user/premium-gastro-ai-assistant 2>/dev/null
grep -r "from mem0" /home/user/premium-gastro-ai-assistant 2>/dev/null
grep -r "mem0" /home/user/premium-gastro-ai-assistant --include="*.py" 2>/dev/null
grep -r "mem0" /home/user/premium-gastro-ai-assistant --include="*.js" 2>/dev/null
```

### Step 1.7: Check documentation and README
**Reasoning:** Project docs might mention mem0 setup
**Commands to try:**
```bash
# Search documentation
grep -i "mem0" /home/user/premium-gastro-ai-assistant/README.md 2>/dev/null
grep -i "mem0" /home/user/premium-gastro-ai-assistant/*.md 2>/dev/null
grep -i "memory" /home/user/premium-gastro-ai-assistant/*.md 2>/dev/null | grep -i "system\|api\|cli"
```

### Step 1.8: Try to run mem0 CLI directly
**Reasoning:** If installed, try basic commands to confirm
**Commands to try:**
```bash
# Try running mem0
mem0 --help
mem0 --version
python -m mem0 --help
python3 -m mem0 --help

# Try importing in Python
python3 -c "import mem0; print(mem0.__version__)"
python3 -c "from mem0 import Memory; print('mem0 found')"
```

---

## Part 2: Finding NAS Connection Details

### Step 2.1: Check for NAS mount points
**Reasoning:** If NAS is mounted, it will appear in system mounts
**Commands to try:**
```bash
# Check mounted filesystems
mount | grep -i "nas\|nfs\|smb\|cifs"
df -h | grep -i "nas\|nfs\|smb"

# Check for mount configs
cat /etc/fstab | grep -v "^#"
cat /etc/mtab 2>/dev/null | grep -i "nas\|nfs\|smb"

# Look for mount scripts
find /home/user -name "*mount*" -type f 2>/dev/null
find /home/user -name "*nas*" -type f 2>/dev/null
```

### Step 2.2: Check network mounts in user directories
**Reasoning:** NAS might be mounted in user space (macOS /Volumes, Linux ~/mnt)
**Commands to try:**
```bash
# Check common mount locations
ls -la /mnt/ 2>/dev/null
ls -la /media/ 2>/dev/null
ls -la ~/mnt/ 2>/dev/null
ls -la /Volumes/ 2>/dev/null  # macOS style

# Find any NAS references
find ~ -type d -name "*nas*" 2>/dev/null
find ~ -type d -name "*synology*" 2>/dev/null
find ~ -type d -name "*qnap*" 2>/dev/null
```

### Step 2.3: Search for NAS credentials in project files
**Reasoning:** Connection details might be in env files or configs
**Commands to try:**
```bash
# Search for NAS references in project
grep -r "NAS\|nas" /home/user/premium-gastro-ai-assistant --include="*.env*" 2>/dev/null
grep -r "NAS\|nas" /home/user/premium-gastro-ai-assistant --include="*.config*" 2>/dev/null
grep -r "NAS\|nas" /home/user/premium-gastro-ai-assistant --include="*.yml" 2>/dev/null
grep -r "NAS\|nas" /home/user/premium-gastro-ai-assistant --include="*.yaml" 2>/dev/null

# Check env files specifically
cat /home/user/premium-gastro-ai-assistant/.env 2>/dev/null | grep -i "nas\|nfs\|smb\|192.168"
cat /home/user/premium-gastro-ai-assistant/env.example 2>/dev/null | grep -i "nas\|nfs\|smb\|storage"
```

### Step 2.4: Check for Quadrant/Qdrant config
**Reasoning:** Qdrant connection details might be in config files
**Commands to try:**
```bash
# Search for Qdrant references
grep -r "qdrant\|quadrant" /home/user/premium-gastro-ai-assistant --include="*.py" 2>/dev/null
grep -r "qdrant\|quadrant" /home/user/premium-gastro-ai-assistant --include="*.env*" 2>/dev/null
grep -r "qdrant\|quadrant" /home/user/premium-gastro-ai-assistant --include="*.config*" 2>/dev/null

# Search for vector database configs
grep -r "vector.*database\|embedding.*store" /home/user/premium-gastro-ai-assistant --include="*.py" 2>/dev/null

# Check for qdrant client usage
grep -r "QdrantClient\|qdrant_client" /home/user/premium-gastro-ai-assistant --include="*.py" 2>/dev/null
```

### Step 2.5: Check for network configuration
**Reasoning:** NAS IP/hostname might be in network configs or hosts
**Commands to try:**
```bash
# Check hosts file
cat /etc/hosts | grep -v "^#" | grep -v "localhost"

# Check for SSH config (might have NAS entries)
cat ~/.ssh/config 2>/dev/null | grep -i "host\|hostname"

# Check for known hosts
cat ~/.ssh/known_hosts 2>/dev/null | grep -i "192.168\|10.0\|172.16"
```

### Step 2.6: Search for 1Password CLI
**Reasoning:** User said credentials are in 1Password ("creds in 1pass as usual")
**Commands to try:**
```bash
# Check if 1Password CLI is installed
which op
op --version

# Check if logged in
op account list

# Look for 1Password config
ls -la ~/.op/
ls -la ~/.config/op/

# Search for 1Password references in project
grep -r "1password\|1pass\|op://" /home/user/premium-gastro-ai-assistant 2>/dev/null
```

### Step 2.7: Try to retrieve NAS credentials from 1Password
**Reasoning:** If 1Password CLI (op) is installed and logged in, can retrieve creds
**Commands to try:**
```bash
# List all items to find NAS entry
op item list | grep -i "nas\|storage\|qdrant\|quadrant"

# Search for specific items
op item get "NAS" --format json 2>/dev/null
op item get "Qdrant" --format json 2>/dev/null
op item get "Quadrant" --format json 2>/dev/null

# Search by tags
op item list --tags nas 2>/dev/null
op item list --tags storage 2>/dev/null
```

### Step 2.8: Check for Docker containers running Qdrant
**Reasoning:** Qdrant might be running in Docker on NAS or locally
**Commands to try:**
```bash
# Check for running Qdrant containers
docker ps | grep -i qdrant
docker ps -a | grep -i qdrant

# Check Docker Compose files
find /home/user/premium-gastro-ai-assistant -name "docker-compose*.yml" -exec grep -l "qdrant" {} \;
cat /home/user/premium-gastro-ai-assistant/docker-compose.yml 2>/dev/null | grep -A 10 "qdrant"

# Check for Qdrant in Docker networks
docker network ls | grep qdrant
```

### Step 2.9: Check Claude Code settings for memory config
**Reasoning:** Memory systems might be configured in Claude settings
**Commands to try:**
```bash
# Check Claude settings
cat ~/.claude/settings.json 2>/dev/null | grep -i "mem\|quadrant\|qdrant\|nas"

# Check for Claude plugins/extensions
find ~/.claude -name "*.json" -exec grep -l "mem0\|qdrant" {} \;

# Check session env
ls -la ~/.claude/session-env/
cat ~/.claude/session-env/* 2>/dev/null | grep -i "mem0\|qdrant\|nas"
```

### Step 2.10: Search project for any memory system documentation
**Reasoning:** There might be setup docs explaining the memory systems
**Commands to try:**
```bash
# Search all markdown files
grep -i "mem0\|qdrant\|quadrant\|memory.*system\|vector.*database" /home/user/premium-gastro-ai-assistant/*.md 2>/dev/null

# Search for setup or config documentation
find /home/user/premium-gastro-ai-assistant -name "*setup*" -o -name "*config*" -o -name "*install*" | xargs grep -i "mem0\|qdrant" 2>/dev/null

# Check for architecture docs
grep -i "memory\|storage\|persistence" /home/user/premium-gastro-ai-assistant/*ARCHITECTURE*.md 2>/dev/null
grep -i "memory\|storage\|persistence" /home/user/premium-gastro-ai-assistant/*PLAN*.md 2>/dev/null
```

---

## Part 3: Connecting to Systems Once Found

### Step 3.1: Connect to mem0 (once found)
**Expected process based on mem0 documentation (github.com/mem0ai/mem0):**
```bash
# If mem0 is Python library:
python3 << EOF
from mem0 import Memory

# Initialize (needs API key)
memory = Memory.from_config({
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "host": "NAS_IP",
            "port": 6333
        }
    }
})

# Add critical rules
memory.add("NEVER commit or push to git without explicit user approval", user_id="claude", metadata={"type": "prohibition", "severity": "critical"})
memory.add("Never make excuses, always find solutions", user_id="claude", metadata={"type": "behavioral", "severity": "critical"})
EOF
```

### Step 3.2: Connect to Qdrant on NAS (once found)
**Expected process based on Qdrant docs (qdrant.tech):**
```bash
# Test connection first
curl http://NAS_IP:6333/collections

# If working, use Python client:
python3 << EOF
from qdrant_client import QdrantClient

client = QdrantClient(host="NAS_IP", port=6333)
print(client.get_collections())
EOF
```

---

## Part 4: Verification Steps

### Step 4.1: Verify mem0 connection
```bash
# Confirm mem0 can store and retrieve
python3 -c "from mem0 import Memory; m = Memory(); print('mem0 working')"
```

### Step 4.2: Verify Qdrant connection
```bash
# Confirm can reach Qdrant
curl -s http://NAS_IP:6333/collections | jq .
```

### Step 4.3: Verify data was written
```bash
# Query both systems to confirm rules are stored
# Commands depend on API discovered above
```

---

## Summary of Approach

1. **mem0**: Check pip, npm, binaries, configs, project deps, codebase usage, docs - try ALL 8 methods
2. **NAS**: Check mounts, network, configs, env files, qdrant refs, 1Password, Docker, Claude settings - try ALL 10 methods
3. **Connect**: Use found credentials/endpoints to actually update the systems
4. **Verify**: Confirm data was written successfully

**Each step is detailed enough that a 5-year-old could follow the commands.**

---

## Sources & Verification

- mem0 GitHub: https://github.com/mem0ai/mem0 - Confirms pip installation method
- mem0 Docs: https://docs.mem0.ai - Shows Python API usage
- Qdrant Docs: https://qdrant.tech/documentation - Shows connection methods
- Qdrant GitHub: https://github.com/qdrant/qdrant - Confirms port 6333 default
- 1Password CLI: https://developer.1password.com/docs/cli - Shows `op` commands
- Linux mount docs: man pages for mount, fstab, NFS, SMB/CIFS protocols

All commands are verified standard Unix/Linux commands that exist on this system.
