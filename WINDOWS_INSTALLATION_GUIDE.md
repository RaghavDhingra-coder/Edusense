# 🪟 EduSence AI - Complete Windows Installation Guide

**Step-by-step guide for installing EduSence AI on Windows 10/11**

This guide assumes **zero prior experience** with Python or command-line tools.

---

## 📋 What You'll Need

- Windows 10 or Windows 11
- Internet connection
- 10GB free disk space
- Administrator access (for some installations)
- 30-45 minutes of time

---

## 🎯 Installation Steps

### Step 1: Install Python (15 minutes)

#### 1.1 Download Python

1. Open your web browser (Chrome, Edge, Firefox)
2. Go to: **https://www.python.org/downloads/**
3. Click the big yellow button: **"Download Python 3.10.x"** (or 3.9.x)
4. Wait for download to complete (usually in Downloads folder)

#### 1.2 Install Python

1. **Find the downloaded file** (e.g., `python-3.10.11-amd64.exe`)
2. **Double-click** to run the installer
3. **⚠️ IMPORTANT**: At the bottom of the installer window, **CHECK the box** that says:
   ```
   ☑ Add Python 3.10 to PATH
   ```
   **This is the most important step!** Don't skip it!

4. Click **"Install Now"**
5. Wait for installation (2-3 minutes)
6. Click **"Close"** when done

#### 1.3 Verify Python Installation

1. Press **Win + R** on your keyboard
2. Type: `cmd` and press **Enter**
3. A black window (Command Prompt) will open
4. Type: `python --version` and press **Enter**
5. You should see: `Python 3.10.x` or `Python 3.9.x`

**If you see an error** like "python is not recognized":
- You forgot to check "Add Python to PATH"
- Solution: Uninstall Python (Control Panel → Programs) and reinstall with the checkbox checked

---

### Step 2: Install Visual C++ Build Tools (10 minutes)

**Why?** Some Python packages need C++ compiler to install.

#### 2.1 Download Build Tools

1. Go to: **https://visualstudio.microsoft.com/visual-cpp-build-tools/**
2. Click **"Download Build Tools"**
3. Wait for download (file: `vs_BuildTools.exe`, ~3MB)

#### 2.2 Install Build Tools

1. **Run** the downloaded file (`vs_BuildTools.exe`)
2. Wait for the installer to load (1-2 minutes)
3. When the installer opens, **select**:
   ```
   ☑ Desktop development with C++
   ```
4. Click **"Install"** (bottom right)
5. Wait for installation (10-15 minutes, downloads ~6GB)
6. Click **"Close"** when done
7. **Restart your computer** (important!)

**Note**: This is a large download. Make sure you have good internet and 10GB free space.

---

### Step 3: Download EduSence AI (5 minutes)

#### Option A: Download ZIP (Easier, No Git Required)

1. Go to the GitHub repository (your project URL)
2. Click the green **"Code"** button
3. Click **"Download ZIP"**
4. Wait for download
5. **Right-click** the ZIP file → **"Extract All"**
6. Choose location (e.g., `C:\EduSence-ai`)
7. Click **"Extract"**

#### Option B: Use Git (If You Have Git Installed)

1. Open Command Prompt (Win + R, type `cmd`, press Enter)
2. Navigate to where you want the project:
   ```cmd
   cd C:\
   ```
3. Clone the repository:
   ```cmd
   git clone https://github.com/yourusername/EduSence-ai.git
   ```
4. Enter the folder:
   ```cmd
   cd EduSence-ai
   ```

**Don't have Git?** Use Option A (Download ZIP) instead.

---

### Step 4: Create Virtual Environment (2 minutes)

**Why?** Keeps project dependencies isolated and organized.

1. **Open Command Prompt**
   - Press **Win + R**
   - Type: `cmd`
   - Press **Enter**

2. **Navigate to project folder**
   ```cmd
   cd C:\EduSence-ai
   ```
   (Replace with your actual path)

3. **Create virtual environment**
   ```cmd
   python -m venv venv
   ```
   Wait 30-60 seconds. You'll see a new `venv` folder created.

4. **Activate virtual environment**
   ```cmd
   venv\Scripts\activate
   ```
   
   You should see `(venv)` appear at the start of your command line:
   ```cmd
   (venv) C:\EduSence-ai>
   ```

**If activation fails:**
- Make sure you're using Command Prompt (cmd.exe), NOT PowerShell
- If using PowerShell, run as Administrator and execute:
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```

---

### Step 5: Install Dependencies (10 minutes)

**This is the longest step.** It downloads and installs all required packages.

1. **Make sure virtual environment is activated** (you should see `(venv)` in prompt)

2. **Upgrade pip** (Python package installer)
   ```cmd
   python -m pip install --upgrade pip
   ```
   Wait 10-20 seconds.

3. **Install all dependencies**
   ```cmd
   pip install -r requirements.txt
   ```
   
   **This will take 5-10 minutes.** You'll see lots of text scrolling. This is normal.
   
   The installer will download and install:
   - PyTorch (~200MB)
   - OpenCV (~50MB)
   - InsightFace (~100MB)
   - MediaPipe (~50MB)
   - Flask and other packages
   
   **Total download: ~500MB**

4. **Wait patiently** until you see:
   ```cmd
   Successfully installed [list of packages]
   (venv) C:\EduSence-ai>
   ```

#### Common Errors During Installation

**Error: "Microsoft Visual C++ 14.0 or greater is required"**
- You skipped Step 2 (Visual C++ Build Tools)
- Go back and install Build Tools
- Restart computer
- Retry this step

**Error: "Access is denied"**
- Close Command Prompt
- Right-click Command Prompt → "Run as administrator"
- Navigate to project folder again
- Retry installation

**Error: "SSL: CERTIFICATE_VERIFY_FAILED"**
- Your network/firewall is blocking downloads
- Try:
  ```cmd
  pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
  ```

**Error: "Could not find a version that satisfies the requirement"**
- Check your Python version: `python --version`
- Must be Python 3.9 or 3.10
- If older, uninstall and install Python 3.10

---

### Step 6: Verify Installation (1 minute)

Test that everything installed correctly:

```cmd
python -c "import torch; import cv2; import insightface; import mediapipe; print('✅ All packages installed successfully!')"
```

**If you see**: `✅ All packages installed successfully!`
- **Success!** You're ready to run the application.

**If you see an error**:
- Note which package failed (e.g., "No module named 'cv2'")
- Install it manually:
  ```cmd
  pip install opencv-python
  ```
- Retry the verification command

---

### Step 7: Run the Application (2 minutes)

1. **Make sure you're in the project folder** with virtual environment activated:
   ```cmd
   (venv) C:\EduSence-ai>
   ```

2. **Start the server**:
   ```cmd
   python integrated_server.py
   ```

3. **Wait for initialization** (30-60 seconds on first run)
   
   You'll see lots of text. Wait for:
   ```
   * Running on http://127.0.0.1:8080
   ```

4. **Open your web browser**
   - Chrome, Edge, or Firefox
   - Go to: **http://localhost:8080**

5. **You should see the EduSence AI dashboard!** 🎉

---

## 🎯 Quick Start After Installation

### Every Time You Want to Use EduSence AI:

1. **Open Command Prompt**
   ```cmd
   Win + R → type "cmd" → Enter
   ```

2. **Navigate to project**
   ```cmd
   cd C:\EduSence-ai
   ```

3. **Activate virtual environment**
   ```cmd
   venv\Scripts\activate
   ```

4. **Start server**
   ```cmd
   python integrated_server.py
   ```

5. **Open browser**
   ```
   http://localhost:8080
   ```

### To Stop the Server:

- Press **Ctrl + C** in Command Prompt
- Type: `deactivate` to exit virtual environment

---

## 🐛 Troubleshooting Common Issues

### Issue: "python is not recognized"

**Solution**:
1. Uninstall Python (Control Panel → Programs → Uninstall)
2. Download Python again from python.org
3. **CHECK "Add Python to PATH"** during installation
4. Restart Command Prompt
5. Test: `python --version`

### Issue: "pip is not recognized"

**Solution**:
```cmd
python -m ensurepip --upgrade
python -m pip install --upgrade pip
```

### Issue: "venv\Scripts\activate" doesn't work

**Solution**:
- Make sure you're using **Command Prompt** (cmd.exe), not PowerShell
- If you must use PowerShell:
  1. Open PowerShell as Administrator
  2. Run: `Set-ExecutionPolicy RemoteSigned`
  3. Close and reopen PowerShell
  4. Try: `.\venv\Scripts\Activate.ps1`

### Issue: Port 8080 already in use

**Solution**:
```cmd
# Find what's using port 8080
netstat -ano | findstr :8080

# Kill the process (replace XXXX with PID from above)
taskkill /PID XXXX /F

# Or change port in integrated_server.py
# Edit line ~60: PORT = 8081
```

### Issue: Camera not working

**Solution**:
1. Check camera permissions:
   - Settings → Privacy → Camera
   - Allow apps to access camera
2. Close other apps using camera (Zoom, Skype, Teams)
3. Try different browser
4. Restart computer

### Issue: "DLL load failed" errors

**Solution**:
1. Install Visual C++ Redistributables:
   - Download: https://aka.ms/vs/17/release/vc_redist.x64.exe
   - Run installer
   - Restart computer

### Issue: Installation is very slow

**Possible causes**:
- Slow internet connection
- Antivirus scanning downloads
- Low disk space

**Solutions**:
- Wait patiently (can take 10-15 minutes)
- Temporarily disable antivirus
- Free up disk space (need 10GB)
- Use wired internet if possible

### Issue: "Access is denied" during installation

**Solution**:
1. Close Command Prompt
2. Right-click Command Prompt icon
3. Select "Run as administrator"
4. Navigate to project folder
5. Retry installation

---

## 📁 Folder Structure After Installation

```
C:\EduSence-ai\
├── venv\                          # Virtual environment (created by you)
├── integrated_server.py           # Main server file
├── requirements.txt               # Dependencies list
├── frontend\                      # Web dashboard files
├── registered_students\           # Student data (created when you register students)
├── sessions\                      # Session data (created when you use camera/video)
└── ... (other files)
```

---

## 💡 Tips for Windows Users

### 1. Use Short Paths
- Install in `C:\EduSence-ai` instead of `C:\Users\YourName\Documents\Projects\...`
- Windows has 260 character path limit

### 2. Use Command Prompt, Not PowerShell
- PowerShell has execution policy restrictions
- Command Prompt (cmd.exe) works better for Python

### 3. Keep Virtual Environment Activated
- Always activate before running: `venv\Scripts\activate`
- You'll see `(venv)` in your prompt when activated

### 4. Disable Antivirus During Installation
- Some antivirus software blocks pip installations
- Re-enable after installation completes

### 5. Restart After Installing Build Tools
- Visual C++ Build Tools require restart
- Don't skip this step

### 6. Check Python Version
- Use Python 3.9 or 3.10
- Python 3.11+ may have compatibility issues
- Python 3.8 or older won't work

---

## 🆘 Still Having Issues?

### Check These:

1. **Python version**: `python --version` (should be 3.9 or 3.10)
2. **Pip version**: `pip --version` (should be 20.0+)
3. **Virtual environment activated**: Look for `(venv)` in prompt
4. **In correct folder**: `dir` should show `integrated_server.py`
5. **Build tools installed**: Check Control Panel → Programs
6. **Antivirus disabled**: Temporarily disable during installation

### Get Help:

- Check GitHub Issues: [Your Repository URL]/issues
- Read full documentation: README.md
- Check troubleshooting section: README.md → Troubleshooting

---

## ✅ Installation Checklist

Use this checklist to track your progress:

- [ ] Python 3.9 or 3.10 installed
- [ ] "Add Python to PATH" was checked during installation
- [ ] `python --version` works in Command Prompt
- [ ] `pip --version` works in Command Prompt
- [ ] Visual C++ Build Tools installed
- [ ] Computer restarted after Build Tools installation
- [ ] Project downloaded (ZIP or Git)
- [ ] Virtual environment created (`python -m venv venv`)
- [ ] Virtual environment activated (`venv\Scripts\activate`)
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Installation verified (test import command worked)
- [ ] Server starts (`python integrated_server.py`)
- [ ] Dashboard opens in browser (http://localhost:8080)

---

## 🎉 Success!

If you've completed all steps and the dashboard opens in your browser, **congratulations!** You've successfully installed EduSence AI on Windows.

**Next steps**:
1. Register some students (http://localhost:8080/register.html)
2. Start the camera and test recognition
3. Upload a video and generate analytics
4. Explore the dashboard features

---

## 📞 Support

If you're still stuck after following this guide:

1. **Check the error message carefully** - it usually tells you what's wrong
2. **Google the error** - many Python errors have common solutions
3. **Check GitHub Issues** - someone may have had the same problem
4. **Ask for help** - create a new GitHub Issue with:
   - Your Windows version
   - Python version (`python --version`)
   - Full error message
   - What step you're stuck on

---

**Made with ❤️ for Windows users who are new to Python**

Good luck! 🚀
