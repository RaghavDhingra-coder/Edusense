# 🪟 Windows Quick Start - EduSence AI

**Get up and running in 10 minutes!**

---

## ⚡ Super Quick Installation (For Experienced Users)

```cmd
# 1. Install Python 3.9/3.10 from python.org (CHECK "Add to PATH")
# 2. Install Visual C++ Build Tools from visualstudio.microsoft.com
# 3. Restart computer

# 4. Open Command Prompt in project folder
cd C:\EduSence-ai

# 5. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate

# 6. Install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

# 7. Run server
python integrated_server.py

# 8. Open browser: http://localhost:8080
```

---

## 🆘 Quick Fixes for Common Errors

### "python is not recognized"
```cmd
# Reinstall Python with "Add to PATH" checked
# Download: https://www.python.org/downloads/
```

### "Microsoft Visual C++ 14.0 required"
```cmd
# Install Build Tools
# Download: https://visualstudio.microsoft.com/visual-cpp-build-tools/
# Select: "Desktop development with C++"
# Restart computer after installation
```

### "Access is denied"
```cmd
# Run Command Prompt as Administrator
# Right-click Command Prompt → "Run as administrator"
```

### "SSL: CERTIFICATE_VERIFY_FAILED"
```cmd
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
```

### Virtual environment won't activate
```cmd
# Use Command Prompt (cmd.exe), NOT PowerShell
# Or in PowerShell as Admin:
Set-ExecutionPolicy RemoteSigned
```

### "DLL load failed"
```cmd
# Install Visual C++ Redistributables
# Download: https://aka.ms/vs/17/release/vc_redist.x64.exe
```

---

## 📋 Pre-Installation Checklist

Before you start, make sure you have:

- [ ] Windows 10 or 11
- [ ] 10GB free disk space
- [ ] Internet connection
- [ ] Administrator access
- [ ] 30 minutes of time

---

## 🎯 Daily Usage (After Installation)

### Starting the Server

```cmd
# 1. Open Command Prompt
Win + R → type "cmd" → Enter

# 2. Go to project folder
cd C:\EduSence-ai

# 3. Activate virtual environment
venv\Scripts\activate

# 4. Start server
python integrated_server.py

# 5. Open browser
# Go to: http://localhost:8080
```

### Stopping the Server

```cmd
# Press Ctrl + C in Command Prompt
# Then type: deactivate
```

---

## 🔧 Useful Commands

### Check Python Version
```cmd
python --version
```

### Check Pip Version
```cmd
pip --version
```

### Update Pip
```cmd
python -m pip install --upgrade pip
```

### Install Single Package
```cmd
pip install package-name
```

### List Installed Packages
```cmd
pip list
```

### Check If Package Installed
```cmd
python -c "import package_name; print('Installed')"
```

### Find Process Using Port 8080
```cmd
netstat -ano | findstr :8080
```

### Kill Process by PID
```cmd
taskkill /PID 1234 /F
```

---

## 📁 Important Folders

```
C:\EduSence-ai\
├── venv\                    # Virtual environment (DON'T DELETE)
├── integrated_server.py     # Main server (RUN THIS)
├── requirements.txt         # Dependencies list
├── frontend\                # Web dashboard
├── registered_students\     # Student data
└── sessions\                # Session data
```

---

## 🌐 Important URLs

- **Dashboard**: http://localhost:8080
- **Registration**: http://localhost:8080/register.html
- **Health Check**: http://localhost:8080/api/health

---

## 💡 Pro Tips

1. **Always activate virtual environment** before running
   - Look for `(venv)` in your prompt

2. **Use short paths** to avoid Windows path length issues
   - Good: `C:\EduSence-ai`
   - Bad: `C:\Users\YourName\Documents\Projects\School\EduSence-ai`

3. **Keep Command Prompt open** while using the application
   - Don't close it or server will stop

4. **Use Command Prompt, not PowerShell**
   - PowerShell has execution policy issues

5. **Restart computer** after installing Visual C++ Build Tools
   - Required for changes to take effect

---

## 🆘 Need More Help?

### Detailed Guides

- **Complete Installation Guide**: [WINDOWS_INSTALLATION_GUIDE.md](WINDOWS_INSTALLATION_GUIDE.md)
- **Full Documentation**: [README.md](README.md)
- **Troubleshooting**: See README.md → Troubleshooting section

### Common Issues

- Python not recognized → Reinstall with "Add to PATH"
- C++ error → Install Visual C++ Build Tools
- Access denied → Run as Administrator
- SSL error → Use `--trusted-host` flag
- DLL error → Install Visual C++ Redistributables

---

## ✅ Quick Test

After installation, test everything works:

```cmd
# Test Python
python --version

# Test packages
python -c "import torch; import cv2; import insightface; print('OK')"

# Start server
python integrated_server.py

# Open browser
# Go to: http://localhost:8080
```

If all steps work, you're ready to go! 🎉

---

## 🎓 First Steps After Installation

1. **Register a student**
   - Go to: http://localhost:8080/register.html
   - Enter name and ID
   - Capture 5-10 photos
   - Click "Register Student"

2. **Test live camera**
   - Go to: http://localhost:8080
   - Click "Start Camera"
   - See real-time face detection

3. **Generate analytics**
   - After camera session
   - Click "Analyze Classroom"
   - View engagement reports

---

**Made for Windows users. Simple. Fast. Effective.** 🚀
