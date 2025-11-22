# RWB Features Guide

This guide covers all the features available in the Researcher's Workbench.

## Voice Interaction

### Speech-to-Text (Listening)

RWB can understand your spoken words and convert them to text.

**How to use:**
1. Click and **hold** the Talk button (or press and hold)
2. Speak your question or command
3. Release the button when finished
4. Wait for the transcription to appear

**Tips for better recognition:**
- Speak at a normal pace
- Enunciate clearly, especially medical terms
- Reduce background noise
- Use a quality microphone

**Status indicators:**
- 🟢 **Green microphone** - Ready to record
- 🔴 **Red microphone** - Recording in progress
- ⏳ **Processing** - Converting speech to text

### Text-to-Speech (Speaking)

RWB reads responses aloud using a natural-sounding voice.

**Controls:**
- **Mute checkbox** - Disable all voice output
- **Stop button** - Interrupt current speech immediately

**Voice behavior:**
- Responses are read sentence by sentence
- Links and code blocks are summarized, not read verbatim
- Technical acronyms are pronounced letter by letter

**When voice is useful:**
- Hands-free operation while reading papers
- Multitasking while getting research updates
- Accessibility needs

**When to mute:**
- In quiet environments (library, office)
- When you prefer reading
- During long text responses

---

## Chat Interface

### Sending Messages

**Voice input:**
1. Hold the Talk button
2. Speak your message
3. Release to send

**Text input:**
1. Type in the text field at the bottom
2. Press **Ctrl+Enter** to send
3. Or click the **Send** button (appears when text is entered)

### Reading Responses

Responses appear in the chat area with:
- **Markdown formatting** - Bold, italic, headers, lists
- **Clickable links** - Open in your default browser
- **Code highlighting** - For technical content
- **Citations** - References from research tools

### Message Types

| Sender | Appearance | Description |
|--------|------------|-------------|
| **You** | Right-aligned, blue | Your questions and commands |
| **Assistant** | Left-aligned, gray | AI responses |
| **System** | Centered, light | Status messages and info |

### Streaming Responses

Responses appear in real-time as they're generated:
- Text streams word by word
- You can read while the response continues
- Use **Stop** to cancel if the response isn't helpful

---

## Research Tools

RWB has access to several research tools that it uses automatically based on your questions.

### PubMed Search

Search the world's largest medical literature database.

**Example queries:**
- "Search PubMed for CRISPR applications in cancer treatment"
- "Find recent studies on Alzheimer's disease biomarkers"
- "What does PubMed say about metformin and longevity?"

**Results include:**
- Article titles with links
- Authors and publication dates
- Journal names
- Abstracts when available
- DOI links

**Tips:**
- Use medical terminology for better results
- Specify date ranges: "studies from the last 5 years"
- Narrow by population: "in pediatric patients"

### Web Search (DuckDuckGo)

Search the internet for general information.

**Example queries:**
- "What are the latest FDA drug approvals?"
- "Search for clinical trial requirements"
- "Find information about medical AI regulations"

**Best for:**
- Current events and news
- General medical information
- Non-academic sources
- Regulatory information

### Wikipedia

Quick access to encyclopedic knowledge.

**Example queries:**
- "What does Wikipedia say about CRISPR?"
- "Look up the history of penicillin"
- "Explain the citric acid cycle"

**Best for:**
- Background information
- Basic explanations
- Historical context
- Quick definitions

### Website Reading

RWB can read and summarize web pages.

**Example queries:**
- "Read this article: [URL]"
- "Summarize the content at [URL]"
- "What does this webpage say about...?"

**Capabilities:**
- Extracts main content from articles
- Ignores ads and navigation
- Summarizes key points

### Python Calculations

For mathematical and computational tasks.

**Example queries:**
- "Calculate the sample size needed for a study with 80% power"
- "Convert 37 degrees Celsius to Fahrenheit"
- "What is the standard deviation of these values: 10, 12, 15, 18, 20?"

---

## File Attachments

Attach files to provide context for your questions.

### Supported File Types

| Type | Extensions | Use Case |
|------|------------|----------|
| **Images** | .png, .jpg, .jpeg | Screenshots, diagrams, figures |
| **Documents** | .pdf, .txt, .docx | Research papers, notes |
| **Markdown** | .md | Formatted notes |

### How to Attach Files

1. Click the **📎 paperclip** button
2. Select one or more files
3. Files appear as a system message
4. Ask your question about the attached files

### Example Uses

- "What does this figure show?" (attach image)
- "Summarize this research paper" (attach PDF)
- "Review my notes and suggest improvements" (attach document)

> **Note:** File processing capabilities are being expanded. Some advanced features may be limited in the current version.

---

## Chat History

### Viewing History

1. Click the **History** tab
2. Browse past conversations in the left panel
3. Click a conversation to view it
4. Scroll through the full conversation

### History Files

- Conversations are saved automatically
- Stored in `~/.rwb/chat_history/`
- Named by date and time: `chat_YYYYMMDD_HHMMSS.json`

### Managing History

**To delete a conversation:**
1. Go to the History tab
2. Right-click on a conversation
3. Select Delete

**History is preserved when:**
- You close the application
- You restart your computer
- You update the application

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| **Ctrl+Enter** | Send text message |
| **Escape** | Cancel current operation (when Stop is visible) |

---

## Status Messages

The status bar shows what RWB is doing:

| Status | Meaning |
|--------|---------|
| **Ready to record** | Waiting for your input |
| **Listening...** | Recording your voice |
| **Processing...** | Working on your request |
| **Speaking...** | Reading the response aloud |
| **Stopped** | Operation was cancelled |

### Understanding Tool Messages

When RWB uses a research tool, you'll see:
1. **"Using tool: [name]"** - Starting the search
2. **Voice feedback** - "OK, researching now" or similar
3. **"Tool call completed"** - Results received
4. **Voice feedback** - "Got results, analyzing now"

---

## Citations and References

When RWB uses research tools, it provides citations.

### Citation Formats

**PubMed citations:**
```
Authors (Year). Title. Journal. DOI: xxx
[Link to PubMed]
```

**Web citations:**
```
Title
URL
```

### Using Citations

- Click links to open the original source
- Citations appear at the end of responses
- Copy links for your reference management software

---

## Conversation Memory

RWB remembers your conversation context:

- **Within a session** - Full conversation history
- **Recent exchanges** - Last 5 exchanges influence responses
- **User context** - Your profile information (from settings)

### Making Use of Memory

**Follow-up questions:**
- "Tell me more about that"
- "What about the side effects?"
- "Can you explain the third point?"

**Building on previous answers:**
- "Now search for papers by that author"
- "Find more recent studies on this topic"
- "What's the opposite viewpoint?"

### Starting Fresh

To start a new conversation topic:
- Simply ask about something completely different
- The assistant will understand the context switch

---

## Advanced Features

### Multi-step Research

RWB can perform complex research tasks:

1. Search multiple sources
2. Synthesize information
3. Provide comprehensive answers

**Example:**
> "Compare what PubMed and recent news say about mRNA vaccines"

RWB will:
1. Search PubMed for academic papers
2. Search the web for news articles
3. Synthesize and compare the findings

### Handling Uncertainty

When RWB isn't sure:
- It will tell you explicitly
- It may ask for clarification
- It will try alternative approaches

**If transcription is unclear:**
> "I'm not sure I understood correctly. Did you mean...?"

---

## Performance Tips

### For Faster Responses

1. Use a smaller AI model for quick questions
2. Keep questions concise
3. Mute TTS if you don't need voice

### For Better Quality

1. Use larger AI models for complex research
2. Provide more context in your questions
3. Use specific medical terminology

### Managing Long Sessions

1. RWB saves history automatically
2. You can close and reopen without losing chat
3. Use History tab to review past research

---

## Feature Summary

| Feature | Status | Description |
|---------|--------|-------------|
| Voice Input | ✅ Full | Speech-to-text with Whisper |
| Voice Output | ✅ Full | Text-to-speech with Kokoro |
| Text Chat | ✅ Full | Type and read responses |
| PubMed Search | ✅ Full | Medical literature search |
| Web Search | ✅ Full | DuckDuckGo integration |
| Wikipedia | ✅ Full | Encyclopedia lookup |
| Website Reading | ✅ Full | Extract web content |
| Python Tools | ✅ Full | Calculations and code |
| File Attachments | 🔄 Partial | Basic support, expanding |
| Chat History | ✅ Full | Save and browse |
| Customization | ✅ Full | User and assistant settings |

---

Next: Learn how to customize your experience in [Settings](SETTINGS.md)
