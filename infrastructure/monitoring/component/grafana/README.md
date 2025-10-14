# Grafana Deployment Setup

This directory contains a complete, portable Grafana deployment setup with Docker that can be easily deployed on any system without manual configuration.

## 🚀 Quick Start

### Option 1: Interactive Script (Recommended)

```bash
# Navigate to the grafana directory
cd infrastructure/monitoring/component/grafana

# Run the interactive control script
./script/grafana-control.sh

# Select options:
# 1. Choose environment (development/staging/production)
# 2. Choose action (start/stop/restart/logs/status)
```

### Option 2: Docker Compose Only

```bash
# Build and start all Grafana environments
docker compose -f dashboard-grafana-compose.yaml up -d --build

# Or start specific environment
docker compose -f dashboard-grafana-compose.yaml up -d grafana-development
```

## 🌍 Multi-Environment Setup

The setup includes three environments:

- **Development**: http://localhost:31001 (port 31001)
- **Staging**: http://localhost:31002 (port 31002)
- **Production**: http://localhost:31003 (port 31003)

## 📁 Project Structure

```
grafana/
├── Dockerfile                    # Custom Grafana image with proper permissions
├── script/grafana-control.sh     # Interactive control script (start/stop/restart/logs/status/build)
├── dashboard-grafana-compose.yaml # Docker Compose configuration (no version attribute)
├── grafana.env                   # Main configuration (admin credentials, settings)
├── grafana-secrets.env           # Additional secrets (if needed)
├── storage/                      # Persistent data storage
│   ├── development/             # Development environment data
│   ├── staging/                # Staging environment data
│   └── production/             # Production environment data
└── .dockerignore                # Docker build exclusions
```

## 🔧 Configuration

### Environment Variables (grafana.env)
```bash
GF_SECURITY_ADMIN_USER=admin
GF_SECURITY_ADMIN_PASSWORD=SuperSecret123!
GF_SECURITY_ALLOW_EMBEDDING=true
GF_USERS_ALLOW_SIGN_UP=false
```

### Ports
- Development: 31001
- Staging: 31002
- Production: 31003

## 🛠️ Interactive Control Script

The `script/grafana-control.sh` provides an interactive menu for easy management:

```bash
cd /path/to/grafana
./script/grafana-control.sh
```

**Available actions:**
- ✅ **start** - Start Grafana containers
- ✅ **stop** - Stop Grafana containers
- ✅ **restart** - Restart Grafana containers
- ✅ **logs** - View container logs
- ✅ **status** - Check container status
- ✅ **build** - Build custom Docker image

**Features:**
- 🔍 **Absolute path detection** - Works from any directory
- 🛡️ **Smart permission handling** - Uses sudo when needed
- 🚀 **Integrated build process** - No separate build script needed
- 📍 **Automatic setup** - Creates directories and files as needed

## 🔒 Security Notes

- Default admin credentials are set in `grafana.env`
- **Change these credentials in production environments**
- The custom Docker image runs Grafana as non-root user (UID 472) for security
- Storage directories have proper permissions set automatically

## 🚀 Deployment on New Systems

This setup is completely portable and requires **zero manual configuration**:

1. **Copy the entire directory** to the new system
2. **Run the control script**: `./script/grafana-control.sh`
3. **Select environment and start** - Everything is set up automatically!

**No manual steps required:**
- ❌ No directory creation needed
- ❌ No permission setting required
- ❌ No build script management
- ❌ No path configuration

## 🔍 Troubleshooting

### Issues Fixed in This Version

✅ **File Path Issues** - Script now uses absolute paths and works from any location  
✅ **Permission Errors** - Smart handling of directory permissions with fallback to sudo  
✅ **Build Context Problems** - Proper Docker build context detection  
✅ **Environment Variables** - Correct loading of configuration files  
✅ **Volume Mounting** - Fixed container-to-host directory permissions  

### Common Solutions

**Permission Issues:**
```bash
# The script handles this automatically with sudo fallbacks
# If needed manually:
sudo chown -R 472:472 storage/
```

**Port Conflicts:**
```bash
# Modify ports in dashboard-grafana-compose.yaml if needed
# Development: 31001, Staging: 31002, Production: 31003
```

**Container Logs:**
```bash
# Using the script (recommended)
./script/grafana-control.sh  # Select "logs" option

# Or manually
docker compose -f dashboard-grafana-compose.yaml logs grafana-development
```

## 📚 Default Access

- **URL**: http://localhost:31001 (or your configured ports)
- **Username**: admin
- **Password**: SuperSecret123!

## 🆙 Upgrading Grafana

To upgrade to a newer Grafana version:

1. **Update version in Dockerfile** (line 1)
2. **Run the control script**: `./script/grafana-control.sh`
3. **Select "build" then "restart"** for each environment

The script handles the entire upgrade process automatically!

## 🎯 Key Improvements

### **Before (Had Issues):**
- ❌ Manual build script management
- ❌ Relative path problems
- ❌ Permission errors
- ❌ Complex multi-step setup

### **After (Fully Automated):**
- ✅ **Single script** handles everything
- ✅ **Absolute paths** work from anywhere
- ✅ **Smart permissions** with sudo fallbacks
- ✅ **Zero configuration** deployment
- ✅ **Integrated build process**
- ✅ **Portable to any system**

## 🚀 Ready to Use

Your Grafana deployment is now:
- 🎯 **Production-ready**
- 🔒 **Secure by default**
- 🚀 **Easy to manage**
- 📦 **Portable**
- 🛠️ **Self-maintaining**

Just run `./script/grafana-control.sh` and select your options! 🎉
