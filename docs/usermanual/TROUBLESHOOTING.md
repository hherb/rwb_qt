# Troubleshooting Guide

This guide helps you solve common problems with the Researcher's Workbench.

## Quick Diagnostic Checklist

Before diving into specific issues, check these common causes:

- [ ] Is Ollama running? (`ollama serve`)
- [ ] Is your microphone connected and permitted?
- [ ] Is your virtual environment activated?
- [ ] Do you have enough free memory?

---

## Installation Issues

### Python Not Found

**Symptom:** `python: command not found` or `python3: command not found`

**Solutions:**

1. **Check Python installation:**
   ```bash
   python3 --version
   # or
   python --version
   ```

2. **Install Python:**
   - macOS: `brew install python@3.12`
   - Ubuntu: `sudo apt install python3.12`
   - Windows: Download from python.org

3. **Add to PATH (Windows):**
   - Reinstall Python
   - Check "Add Python to PATH" during installation

### PortAudio Installation Failed

**Symptom:** `Could not find portaudio` during pip install

**Solutions:**

**macOS:**
```bash
brew install portaudio
pip install pyaudio
```

**Ubuntu/Debian:**
```bash
sudo apt-get install portaudio19-dev python3-dev
pip install pyaudio
```

**Windows:**
```bash
# Usually works without additional steps
pip install pyaudio

# If it fails, try:
pip install pipwin
pipwin install pyaudio
```

### Dependency Conflicts

**Symptom:** Version conflicts during `pip install`

**Solutions:**

1. **Create fresh virtual environment:**
   ```bash
   rm -rf .venv
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -e .
   ```

2. **Update pip:**
   ```bash
   pip install --upgrade pip
   ```

3. **Install with no cache:**
   ```bash
   pip install --no-cache-dir -e .
   ```

---

## Startup Issues

### Application Won't Start

**Symptom:** Nothing happens when running `python -m rwb`

**Check these:**

1. **Virtual environment active:**
   ```bash
   which python  # Should show .venv path
   ```

2. **Dependencies installed:**
   ```bash
   pip list | grep PySide6
   pip list | grep fastrtc
   ```

3. **Run with verbose output:**
   ```bash
   python -m rwb 2>&1 | tee startup.log
   ```

### Qt Plugin Error (macOS)

**Symptom:**
```
Could not find the Qt platform plugin "cocoa"
```

**Solutions:**

1. **The app should handle this automatically**, but if not:
   ```bash
   pip install --force-reinstall PySide6
   ```

2. **Set Qt plugin path manually:**
   ```bash
   export QT_QPA_PLATFORM_PLUGIN_PATH=$(python -c "import PySide6; print(PySide6.__path__[0])")/Qt/plugins
   ```

3. **Check installation:**
   ```bash
   python -c "from PySide6.QtWidgets import QApplication; print('OK')"
   ```

### Window Appears Then Disappears

**Symptom:** Window flashes briefly then closes

**Check console output:**
```bash
python -m rwb
# Look for error messages
```

**Common causes:**
- Ollama not running
- Missing audio device
- Corrupted settings

**Try resetting settings:**
```bash
# macOS/Linux
rm -rf ~/.config/RWB

# Then restart
python -m rwb
```

---

## Ollama Issues

### Ollama Not Running

**Symptom:**
```
Error: connection refused
```
or
```
Error: could not connect to Ollama
```

**Solutions:**

1. **Start Ollama:**
   ```bash
   ollama serve
   ```

2. **Check if running:**
   ```bash
   curl http://localhost:11434/api/tags
   # Should return JSON with models
   ```

3. **On macOS**, Ollama might be running as a menu bar app. Check for the llama icon.

### Model Not Found

**Symptom:**
```
model 'xyz' not found
```

**Solutions:**

1. **List available models:**
   ```bash
   ollama list
   ```

2. **Download the model:**
   ```bash
   ollama pull qwen2.5:14b-instruct-q8_0
   ```

3. **Check model name in Settings:**
   - Open Settings → Model tab
   - Select an installed model

### Slow Responses

**Symptom:** Responses take very long or system becomes unresponsive

**Solutions:**

1. **Use a smaller model:**
   ```bash
   ollama pull qwen2.5:7b-instruct-q4_0
   ```
   Then select it in Settings.

2. **Check memory usage:**
   - macOS: Activity Monitor → Memory
   - Linux: `htop` or `free -h`
   - Windows: Task Manager → Performance

3. **Close other applications** to free memory

4. **Restart Ollama:**
   ```bash
   # Stop Ollama
   pkill ollama

   # Start again
   ollama serve
   ```

### Out of Memory

**Symptom:**
```
error: out of memory
```
or system becomes very slow

**Solutions:**

1. **Use a smaller/more quantized model:**
   - `7b` instead of `14b`
   - `q4` instead of `q8`

2. **Close memory-intensive applications**

3. **Increase swap space (Linux):**
   ```bash
   sudo fallocate -l 8G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   ```

---

## Audio Issues

### Microphone Not Working

**Symptom:** No text appears after releasing Talk button

**Solutions:**

1. **Check microphone permissions:**
   - **macOS:** System Preferences → Security & Privacy → Privacy → Microphone
   - **Windows:** Settings → Privacy → Microphone
   - **Linux:** Check PulseAudio/PipeWire settings

2. **Test microphone:**
   ```bash
   # Record a test
   python -c "
   import pyaudio
   p = pyaudio.PyAudio()
   for i in range(p.get_device_count()):
       info = p.get_device_info_by_index(i)
       if info['maxInputChannels'] > 0:
           print(f'{i}: {info[\"name\"]}')
   "
   ```

3. **Check default input device** in system sound settings

4. **Try a different microphone** if available

### No Sound Output

**Symptom:** No voice response, but text appears

**Solutions:**

1. **Check Mute checkbox** - Make sure it's unchecked

2. **Check system volume** - Not muted, volume up

3. **Test speakers:**
   ```bash
   python -c "
   import pyaudio
   p = pyaudio.PyAudio()
   for i in range(p.get_device_count()):
       info = p.get_device_info_by_index(i)
       if info['maxOutputChannels'] > 0:
           print(f'{i}: {info[\"name\"]}')
   "
   ```

4. **Check default output device** in system settings

### Audio Crackling or Stuttering

**Symptom:** Voice output is choppy or distorted

**Solutions:**

1. **Close other audio applications**

2. **Check CPU usage** - High CPU can cause audio issues

3. **Try a different audio device** if available

4. **Reduce system load:**
   - Use a smaller AI model
   - Close background applications

### Speech Recognition Inaccurate

**Symptom:** Transcription doesn't match what you said

**Solutions:**

1. **Speak more clearly** and at a moderate pace

2. **Reduce background noise:**
   - Close windows
   - Move away from fans/AC
   - Use a headset

3. **Check microphone quality:**
   - Built-in laptop mics are often poor
   - Consider an external USB microphone

4. **Hold button longer** - Wait for a moment of silence before releasing

---

## Interface Issues

### Text Not Displaying Correctly

**Symptom:** Garbled text, missing characters, or formatting issues

**Solutions:**

1. **Restart the application**

2. **Clear chat and try again**

3. **Check font installation:**
   ```bash
   fc-list | grep -i "mono"  # Linux
   ```

### Buttons Not Responding

**Symptom:** Clicking buttons does nothing

**Solutions:**

1. **Check status message** - May be processing

2. **Click Stop** to cancel any pending operations

3. **Restart the application**

### Window Size/Position Not Saved

**Symptom:** Window resets to default size each launch

**Solutions:**

1. **Close properly** - Don't force quit

2. **Check config permissions:**
   ```bash
   # Linux
   ls -la ~/.config/RWB/

   # macOS
   ls -la ~/Library/Preferences/com.rwb.*
   ```

3. **Delete and recreate settings:**
   ```bash
   rm -rf ~/.config/RWB  # Linux
   defaults delete RWB    # macOS
   ```

---

## Research Tool Issues

### PubMed Search Not Working

**Symptom:** "Error" or no results from PubMed searches

**Solutions:**

1. **Check internet connection**

2. **Set your email in Settings:**
   - Open Settings → User tab
   - Enter valid email address
   - NCBI requires email for API access

3. **Try a simpler query:**
   ```
   "Search PubMed for cancer"
   ```

4. **Check NCBI status:** [NCBI Status Page](https://www.ncbi.nlm.nih.gov/status/)

### Web Search Not Working

**Symptom:** Web searches fail or return errors

**Solutions:**

1. **Check internet connection**

2. **Try again** - May be rate limited

3. **Use different wording:**
   ```
   "Search the web for..." instead of "Google..."
   ```

4. **DuckDuckGo may have temporary issues** - Wait and retry

### Wikipedia Not Found

**Symptom:** Wikipedia lookups fail

**Solutions:**

1. **Check internet connection**

2. **Try exact article names:**
   ```
   "Look up CRISPR on Wikipedia"
   ```

3. **The topic may not have a Wikipedia article**

---

## Performance Issues

### High CPU Usage

**Symptom:** Application uses excessive CPU

**Solutions:**

1. **Check if actively processing** - CPU usage is normal during inference

2. **Use a smaller model** for less CPU load

3. **Check for runaway processes:**
   ```bash
   top | grep python
   ```

4. **Restart Ollama** to release GPU/CPU resources

### High Memory Usage

**Symptom:** Application or Ollama uses too much RAM

**Solutions:**

1. **Use smaller models:**
   - `7b` models use ~4-8GB
   - `14b` models use ~8-16GB

2. **Use more quantized models:**
   - `q4_0` uses less memory than `q8_0`

3. **Restart Ollama** between sessions to free memory

### Application Freezing

**Symptom:** UI becomes unresponsive

**Solutions:**

1. **Wait** - Long operations may freeze UI temporarily

2. **Click Stop** if available

3. **Check memory** - May be swapping

4. **Force quit and restart:**
   ```bash
   pkill -f "python -m rwb"
   ```

---

## Data Issues

### Chat History Missing

**Symptom:** Previous conversations not showing in History tab

**Solutions:**

1. **Check history directory:**
   ```bash
   ls ~/.rwb/chat_history/
   ```

2. **Files may be corrupted:**
   ```bash
   # Check for valid JSON
   python -c "import json; json.load(open('~/.rwb/chat_history/chat_xxx.json'))"
   ```

3. **Permissions issue:**
   ```bash
   chmod 755 ~/.rwb/chat_history/
   chmod 644 ~/.rwb/chat_history/*.json
   ```

### Settings Reset

**Symptom:** Settings return to defaults unexpectedly

**Solutions:**

1. **Check for permission issues** in config directory

2. **Don't force quit** - Always close properly

3. **Corruption** - Delete and reconfigure:
   ```bash
   rm -rf ~/.config/RWB  # Linux
   ```

---

## Getting More Help

### Collecting Debug Information

When reporting issues, include:

1. **System information:**
   ```bash
   uname -a                    # OS info
   python --version            # Python version
   pip list | grep -E "PySide|fastrtc|ollama"  # Key packages
   ollama list                 # Available models
   ```

2. **Console output:**
   ```bash
   python -m rwb 2>&1 | tee debug.log
   ```

3. **Steps to reproduce** the issue

### Log Locations

| Information | Location |
|-------------|----------|
| Console output | Terminal where you ran the app |
| Settings | `~/.config/RWB/` (Linux) |
| Chat history | `~/.rwb/chat_history/` |
| Ollama logs | `~/.ollama/logs/` |

### Common Error Messages

| Error | Meaning | Solution |
|-------|---------|----------|
| `Connection refused` | Ollama not running | Start `ollama serve` |
| `Model not found` | Model not downloaded | `ollama pull model-name` |
| `Out of memory` | Insufficient RAM | Use smaller model |
| `Permission denied` | File access issue | Check permissions |
| `No audio device` | Microphone issue | Check audio settings |

---

## Still Having Issues?

1. **Search existing issues** in the project repository
2. **Check recent commits** for related fixes
3. **Try the latest version** of the application
4. **Report the issue** with debug information collected above
