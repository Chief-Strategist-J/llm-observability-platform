# Required Keys for Deployment

## Core Application Keys (REQUIRED)

### 1. Cloudflare Workers AI
**Purpose**: Run AI models

**Get Keys**:
1. Go to https://dash.cloudflare.com
2. Copy Account ID from URL: `https://dash.cloudflare.com/{ACCOUNT_ID}/...`
3. Go to "API Tokens" in profile
4. Create token with "Workers AI" permissions

**Add to `.env.llm_chat_app`**:
```bash
CLOUDFLARE_ACCOUNT_ID=
CLOUDFLARE_API_TOKEN=
```

**Status**: ✅ Already configured in your env

---

## Deployment Platform Keys (Choose ONE)

### Option 1: Railway.app (Recommended)
**Purpose**: Deploy app to cloud (FREE $5/month)

**Get Key**:
```bash
npm install -g @railway/cli
railway login
```

**No manual key needed** - CLI handles authentication

**Add to `.env.llm_chat_app`** (optional):
```bash
RAILWAY_TOKEN=
```

---

### Option 2: Render.com
**Purpose**: Deploy app to cloud (FREE 750 hours/month)

**Get Key**:
1. Go to https://dashboard.render.com
2. Account Settings → API Keys
3. Create new API key

**Add to `.env.llm_chat_app`**:
```bash
RENDER_API_KEY=rnd_xxxxxxxxxxxxxxxxxxxxxx
```

---

### Option 3: Fly.io
**Purpose**: Deploy app to cloud (FREE 3 VMs)

**Get Key**:
```bash
curl -L https://fly.io/install.sh | sh
fly auth login
```

**No manual key needed** - CLI handles authentication

---

## Knowledge Graph Database Keys (OPTIONAL)

### Option 1: Neo4j Aura Free Tier (Online - Recommended)
**Purpose**: Cloud-based knowledge graph (FREE tier available)

**Get Keys**:
1. Go to https://console.neo4j.io
2. Create account
3. Go to "API Access" in settings
4. Generate Client ID and Client Secret

**Add to `.env.llm_chat_app`**:
```bash
NEO4J_AURA_API_KEY=your_client_id_here
NEO4J_AURA_API_SECRET=your_client_secret_here
```

**After creating instance via API**:
```bash
NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=generated_password_from_api
```

---

### Option 2: Local Neo4j (Offline)
**Purpose**: Local Docker-based knowledge graph

**Already configured**:
```bash
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
```

**Status**: ✅ Already working in your setup

---

## Complete Environment Variables Summary

### Minimum Required (App Only)
```bash
CLOUDFLARE_ACCOUNT_ID=
CLOUDFLARE_API_TOKEN=
```

### With Local Neo4j (Current Setup)
```bash
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

CLOUDFLARE_ACCOUNT_ID=
CLOUDFLARE_API_TOKEN=
```

### With Neo4j Aura (Cloud)
```bash
NEO4J_AURA_API_KEY=your_api_key
NEO4J_AURA_API_SECRET=your_api_secret
NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=generated_password

CLOUDFLARE_ACCOUNT_ID=
CLOUDFLARE_API_TOKEN=
```

### For Railway Deployment
```bash
CLOUDFLARE_ACCOUNT_ID=
CLOUDFLARE_API_TOKEN=
```

### For Render Deployment
```bash
RENDER_API_KEY=

CLOUDFLARE_ACCOUNT_ID=
CLOUDFLARE_API_TOKEN=
```

---

## Verification Commands

### Test Cloudflare Connection
```bash
curl -X GET "https://api.cloudflare.com/client/v4/accounts/<Account ID>/ai/models/search" \
  -H "Authorization: Bearer <API Token>"
```

**Expected**: JSON with list of models

### Test Neo4j Local Connection
```bash
docker exec -it neo4j-development cypher-shell -u neo4j -p password "RETURN 1"
```

**Expected**: `1`

### Test Neo4j Aura Connection
```bash
python3 -c "
from neo4j import GraphDatabase
driver = GraphDatabase.driver('neo4j+s://xxxxx.databases.neo4j.io', auth=('neo4j', 'password'))
driver.verify_connectivity()
print('Connected!')
"
```

---

## What Each Key Does

| Key | Purpose | Required For | Free Tier |
|-----|---------|--------------|-----------|
| `CLOUDFLARE_ACCOUNT_ID` | Access Cloudflare AI models | Core app | ✅ Yes |
| `CLOUDFLARE_API_TOKEN` | Authenticate with Cloudflare | Core app | ✅ Yes |
| `NEO4J_URI` | Connect to knowledge graph | Knowledge graph | ✅ Local/Aura |
| `NEO4J_USER` | Neo4j authentication | Knowledge graph | ✅ Yes |
| `NEO4J_PASSWORD` | Neo4j authentication | Knowledge graph | ✅ Yes |
| `NEO4J_AURA_API_KEY` | Create Aura instances | Auto-provision | ✅ Yes |
| `NEO4J_AURA_API_SECRET` | Create Aura instances | Auto-provision | ✅ Yes |
| `RENDER_API_KEY` | Deploy to Render | Render deployment | ✅ Yes |
| `RAILWAY_TOKEN` | Deploy to Railway | Railway deployment | ✅ Yes |

---

## Current Status

✅ **Working**: Cloudflare AI (your keys are valid)  
✅ **Working**: Local Neo4j (running in Docker)  
❌ **Missing**: Deployment platform keys (optional)  
❌ **Missing**: Neo4j Aura keys (optional)

---

## Quick Start Options

### Option A: Use Current Setup (No New Keys)
Your current env works perfectly! Just deploy:
```bash
docker-compose up --build -d
```

### Option B: Deploy to Railway (Free)
```bash
railway login
railway up
```
Railway CLI handles authentication automatically.

### Option C: Use Neo4j Aura (Free Cloud Database)
1. Get keys from https://console.neo4j.io
2. Add `NEO4J_AURA_API_KEY` and `NEO4J_AURA_API_SECRET` to env
3. Run workflow to create instance

---

## Security Notes

- ✅ Keep `.env.llm_chat_app` out of git (already in `.gitignore`)
- ✅ Never commit API keys
- ✅ Rotate tokens regularly
- ✅ Use environment-specific credentials for prod/dev

---

## Need Help?

**Cloudflare Keys**: https://dash.cloudflare.com  
**Neo4j Aura**: https://console.neo4j.io  
**Railway**: https://railway.app  
**Render**: https://render.com  
**Fly.io**: https://fly.io