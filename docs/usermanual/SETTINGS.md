# Settings and Customization Guide

This guide explains all the settings available in RWB and how to customize your experience.

## Accessing Settings

Click the **Settings button** (⚙️ gear icon) in the top-left corner of the application window.

The Settings dialog has three tabs:
1. **User** - Your personal information
2. **Assistant** - Assistant personality settings
3. **Model** - AI model and voice selection

---

## User Settings

Configure your personal information to get personalized responses.

### User Profile Fields

| Field | Description | Example |
|-------|-------------|---------|
| **Title** | Your professional title | Dr., Prof., Mr., Ms. |
| **First Name** | Your first name | Jane |
| **Last Name** | Your surname | Smith |
| **Email** | Your email address | jane.smith@university.edu |
| **Background** | Brief description of your expertise | "Biomedical researcher specializing in oncology" |

### Why Set User Information?

**Personalized greetings:**
> "Good morning, Dr. Smith!"

**Contextual responses:**
- The assistant knows your expertise level
- Responses are tailored to your background
- Medical terminology is used appropriately

**PubMed searches:**
- Your email is used for NCBI Entrez API identification
- Required for programmatic access to PubMed

### Example User Profiles

**Academic Researcher:**
```
Title: Dr.
First Name: Maria
Last Name: Garcia
Email: m.garcia@research-institute.org
Background: Molecular biologist with 10 years experience
in cancer research, specializing in tumor immunology.
```

**Clinical Professional:**
```
Title: Dr.
First Name: James
Last Name: Wilson
Email: jwilson@hospital.org
Background: Internal medicine physician with interest
in evidence-based practice and clinical decision support.
```

**Graduate Student:**
```
Title: Mr.
First Name: Alex
Last Name: Chen
Email: alex.chen@university.edu
Background: PhD candidate in neuroscience, researching
Alzheimer's disease biomarkers.
```

---

## Assistant Settings

Customize the AI assistant's personality and behavior.

### Assistant Fields

| Field | Description | Example |
|-------|-------------|---------|
| **Name** | Assistant's name | Emily, Max, Research Assistant |
| **Background** | Assistant's persona | "Medical research specialist" |
| **Base Prompt** | Additional instructions | Custom behavior rules |

### Changing the Assistant Name

The default name is "Emily." You can change it to:
- A different name you prefer
- A functional name like "Research Assistant"
- Any name that helps you identify the assistant

The assistant will:
- Introduce itself by this name
- Respond when addressed by this name

### Customizing the Background

The background field shapes the assistant's expertise and response style.

**Default:**
> "I am an AI research assistant specialized in medical and scientific research."

**Example customizations:**

**For clinical focus:**
> "I am a clinical research assistant with expertise in interpreting medical literature, understanding clinical trials, and explaining treatment options in accessible language."

**For basic science:**
> "I am a laboratory research assistant specializing in molecular biology, biochemistry, and experimental design. I help with protocol optimization and data interpretation."

**For literature review:**
> "I am a systematic review specialist. I help identify relevant studies, assess quality, and synthesize findings across multiple papers."

### Base Prompt (Advanced)

The base prompt adds custom instructions that apply to all conversations.

**Use cases:**
- Specific formatting requirements
- Domain-specific terminology preferences
- Response style guidelines

**Example base prompts:**

**Concise responses:**
```
Always provide concise answers. Use bullet points for lists.
Limit responses to 3-4 paragraphs unless asked for more detail.
```

**Academic style:**
```
Use formal academic language. Always cite sources when available.
Mention limitations and uncertainties in research findings.
```

**Teaching mode:**
```
Explain concepts as if teaching a graduate student.
Define technical terms when first used.
Provide analogies for complex concepts.
```

---

## Model Settings

Select the AI model and voice for the assistant.

### AI Model Selection

Choose from available Ollama models installed on your system.

**Model naming convention:**
```
model-name:size-variant
Example: qwen2.5:14b-instruct-q8_0
```

**Size indicators:**
- **7b, 8b** - Smaller, faster, less capable
- **14b** - Medium, good balance
- **32b, 70b** - Larger, slower, more capable

**Quantization (q4, q8):**
- **q4** - More compressed, faster, slightly less accurate
- **q8** - Less compressed, slower, more accurate

### Recommended Models

| Use Case | Model | Requirements |
|----------|-------|--------------|
| **Quick queries** | `qwen2.5:7b-instruct-q4_0` | 8GB RAM |
| **General use** | `qwen2.5:14b-instruct-q8_0` | 16GB RAM |
| **Complex research** | `qwen2.5:32b-instruct-q4_0` | 32GB RAM |

### Changing Models

1. Open Settings
2. Go to the Model tab
3. Select a model from the dropdown
4. Click OK

**Note:** You must have the model downloaded in Ollama first:
```bash
ollama pull model-name
```

### TTS Voice Selection

Choose the voice used for text-to-speech output.

**Available voices (Kokoro):**
| Voice ID | Description |
|----------|-------------|
| `bf_emma` | Female, British English (default) |
| `af_sarah` | Female, American English |
| `am_michael` | Male, American English |
| `bf_isabella` | Female, British English |

**Changing the voice:**
1. Open Settings
2. Go to the Model tab
3. Select a voice from the dropdown
4. Click OK

The new voice takes effect immediately for new responses.

---

## Quick Settings (Toolbar)

Some settings are available directly in the main window:

### Mute Checkbox

Located next to the Settings button.

**When checked:**
- All text-to-speech is disabled
- Responses appear in text only
- Useful in quiet environments

**When unchecked:**
- Responses are read aloud
- Normal voice interaction

### Window Size and Position

RWB remembers:
- Window size
- Window position on screen
- History panel split position

These are saved automatically when you close the application.

---

## Settings Storage

### Where Settings Are Stored

Settings are stored using your operating system's standard location:

| OS | Location |
|----|----------|
| **macOS** | `~/Library/Preferences/` |
| **Linux** | `~/.config/RWB/` |
| **Windows** | Windows Registry |

### Chat History Location

Chat conversations are stored at:
```
~/.rwb/chat_history/
```

Files are named by timestamp:
```
chat_20251122_143052.json
```

### Backing Up Settings

**To back up your settings:**

*macOS:*
```bash
cp ~/Library/Preferences/com.rwb.* ~/backup/
```

*Linux:*
```bash
cp -r ~/.config/RWB ~/backup/
```

**To back up chat history:**
```bash
cp -r ~/.rwb/chat_history ~/backup/
```

---

## Environment Variables

Advanced users can set environment variables to override defaults.

### Available Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DEFAULT_MODEL` | Default AI model | `qwen2.5:14b-instruct-q8_0` |
| `AUTHOR_EMAIL` | Email for NCBI API | `default@example.com` |

### Setting Environment Variables

**macOS/Linux (temporary):**
```bash
export DEFAULT_MODEL="qwen2.5:7b-instruct-q4_0"
python -m rwb
```

**macOS/Linux (permanent):**
Add to `~/.bashrc` or `~/.zshrc`:
```bash
export DEFAULT_MODEL="qwen2.5:7b-instruct-q4_0"
export AUTHOR_EMAIL="your.email@example.com"
```

**Windows (Command Prompt):**
```cmd
set DEFAULT_MODEL=qwen2.5:7b-instruct-q4_0
python -m rwb
```

---

## Resetting Settings

### Reset Individual Settings

1. Open Settings
2. Clear the field or select the default option
3. Click OK

### Reset All Settings

**macOS:**
```bash
defaults delete RWB
rm -rf ~/.rwb/
```

**Linux:**
```bash
rm -rf ~/.config/RWB
rm -rf ~/.rwb/
```

**Windows:**
1. Open Registry Editor (regedit)
2. Navigate to `HKEY_CURRENT_USER\Software\RWB`
3. Delete the RWB key
4. Delete `%USERPROFILE%\.rwb\`

> **Warning:** This will delete all settings and chat history!

---

## Best Practices

### For Researchers

1. **Set your background accurately** - Helps get appropriate response depth
2. **Use your institutional email** - Required for some API access
3. **Choose an appropriate model** - Balance speed and capability

### For Clinical Users

1. **Note your clinical focus** - Gets relevant literature
2. **Consider privacy** - All processing is local
3. **Customize the base prompt** - Add reminders about evidence quality

### For Students

1. **Mention your level** - "Graduate student" helps calibrate explanations
2. **Use teaching mode** - Add base prompt for educational responses
3. **Start with smaller models** - Faster for learning and exploration

---

## Troubleshooting Settings

### Settings Not Saving

1. Check write permissions to config directory
2. Ensure application closes properly (don't force quit)
3. Try running as administrator (Windows)

### Model Not Appearing

1. Verify model is downloaded: `ollama list`
2. Ensure Ollama server is running
3. Restart the application

### Voice Not Changing

1. New voice applies to new responses only
2. Stop current TTS and try again
3. Check that the voice ID is valid

---

Next: [Troubleshooting Guide](TROUBLESHOOTING.md) for common issues and solutions
