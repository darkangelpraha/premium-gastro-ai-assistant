# How to Run Bluejet Explorer Securely

## 🔒 Security Approach

This script **NEVER stores credentials** in files. It fetches them from 1Password on-demand using the `op` CLI.

---

## ✅ Run on Your Mac

**Why:** The `op` command is installed on your Mac at `/usr/local/bin/op`

### Steps:

1. **Copy the script to your Mac** (if not already there):
   The file is: `explore_bluejet_secure.py`

2. **Install required Python packages** (one-time):
   ```bash
   pip3 install beautifulsoup4 requests
   ```

3. **Run the script**:
   ```bash
   python3 explore_bluejet_secure.py
   ```

4. **Authenticate with 1Password** (if prompted):
   The `op` command will ask for your 1Password authentication

5. **Review the output**:
   - The script will log in to Bluejet
   - Extract high-level structure
   - Save HTML to `/tmp/bluejet_dashboard.html`
   - Show what's available in Bluejet

---

## 🔐 Security Features

✅ **Credentials fetched from 1Password on-demand**
- Never stored in `.env` files
- Never committed to Git
- Cleared from memory immediately after use

✅ **1Password CLI used for all secrets**
- Item IDs: `xiddgpu4fnwdvx37xiwjdzz3de` (API Key)
- Item IDs: `dr7o5x765zikuy52kdspkalone` (Login)
- Vault: `AI`

✅ **No plaintext credentials anywhere**
- Code only contains 1Password references
- Safe to commit to Git

---

## 📋 What It Will Show You

The script will display:
- Page title and main sections
- Navigation menu items
- Available features
- Data tables and forms
- High-level overview of Bluejet capabilities

This helps us understand what Bluejet does so we can:
1. Document your workflows
2. Create custom Claude skills
3. Build API integrations

---

## ❌ Do NOT Run in Container

This script requires the `op` command which is installed on your Mac, not in the Docker/container environment.

**Always run on your Mac where `op` is available.**

---

## 🆘 Troubleshooting

**"op: command not found"**
→ Make sure you're running on your Mac, not in a container

**"Authentication required"**
→ Run: `/usr/local/bin/op signin`

**"Permission denied"**
→ Run: `chmod +x explore_bluejet_secure.py`

---

Ready to run it? Execute this on your Mac:

```bash
python3 explore_bluejet_secure.py
```
