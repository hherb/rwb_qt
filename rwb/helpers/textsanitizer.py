
import re

tts_replacements = {
    "Dr.": "Doctor",
    "Mr.": "Mister",
    "i.e.": "that is",
    "I.e.": "That is",
    "e.g.": "for example",
    "etc.": "and so on",
    "vs.": "versus",
    "a.k.a.": "also known as",
    # Add more replacements as needed
}

# Pre-compile regex patterns
CONSECUTIVE_LINKS_PATTERN = re.compile(r'(\[.*?\]\(.*?\)[\s]*){2,}')
SINGLE_LINK_PATTERN = re.compile(r'\[.*?\]\(.*?\)')
IMAGE_PATTERN = re.compile(r'!\[.*?\]\(.*?\)')  # Images with alt text
INLINE_IMAGE_PATTERN = re.compile(r'<img.*?>')  # HTML image tags
CODE_BLOCK_PATTERN = re.compile(r'```[\s\S]*?```')
INLINE_CODE_PATTERN = re.compile(r'`[^`]*?`')
HEADER_PATTERN = re.compile(r'^\s*#{1,6}\s+.*$', re.MULTILINE)
BOLD_ASTERISK_PATTERN = re.compile(r'\*\*([^*]*)\*\*')
BOLD_UNDERSCORE_PATTERN = re.compile(r'__([^_]*)__')
ITALIC_ASTERISK_PATTERN = re.compile(r'\*([^*]*)\*')
ITALIC_UNDERSCORE_PATTERN = re.compile(r'_([^_]*)_')
BLOCKQUOTE_PATTERN = re.compile(r'^>\s+', re.MULTILINE)
HTML_TAG_PATTERN = re.compile(r'<[^>]*>')
BULLET_LIST_PATTERN = re.compile(r'^\s*[-*+]\s+', re.MULTILINE)
NUMBERED_LIST_PATTERN = re.compile(r'^\s*\d+\.\s+', re.MULTILINE)
HORIZONTAL_RULE_PATTERN = re.compile(r'^-{3,}$|^\*{3,}$|^_{3,}$', re.MULTILINE)
TABLE_PATTERN = re.compile(r'\|.*\|')
TABLE_SEPARATOR_PATTERN = re.compile(r'^\s*[-:]+\s*$', re.MULTILINE)
WHITESPACE_PATTERN = re.compile(r'\s+')
ESCAPED_CHAR_PATTERN = re.compile(r'\\([\\`*_{}[\]()#+-.!])')
# Add pattern to detect missing spaces between words
WORD_BOUNDARY_PATTERN = re.compile(r'([a-z])([A-Z][a-z])')
URL_PATTERN = re.compile(
    r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+(?:/[-\w%!.~\'()*+,;=:@/&?={}#]*)?'
)

# Medical acronyms to be spoken letter by letter
MEDICAL_ACRONYMS = [
    # General Medical Acronyms
    "ABG", "ACE", "ACLS", "ADR", "AED", "ALS", "AMA", "ARDS", "BLS", "BMI",
    "BMP", "BP", "BPM", "CBC", "CHF", "CKD", "CMO", "CNS", "COPD", "CPR",
    "CSF", "CT", "CVA", "CXR", "DNR", "DOA", "DVT", "ECG", "EKG", "ED",
    "EEG", "EMR", "ENT", "ER", "GCS", "GI", "HEENT", "HIV", "HR", "ICU",
    "IM", "IV", "KVO", "LOC", "LOS", "LP", "MAR", "MI", "MRI", "MRSA",
    "NG", "NPO", "NSAID", "OB", "GYN", "OR", "PCA", "PE", "PERRLA", "PMH",
    "PO", "PPE", "PRN", "PT", "PTT", "PVC", "RACGP", "RBC", "ROS", "RR",
    "SBAR", "SOB", "STAT", "STD", "TIA", "TPN", "TSH", "UA", "UTI", "VF",
    "VS", "VT", "WBC", "WNL",
    
    # Emergency Medicine Specific
    "ACEP", "ACS", "ACEM", "BVM", "DKA", "EMS", "ESI", "ETT", "FAST", "GSW",
    "ICP", "LMA", "MVA", "PEA", "POCUS", "ROSC", "RSI", "STEMI", "TBSA", "TCA",
    
    # Health IT and Machine Learning Related
    "AI", "API", "CDS", "CDSS", "CPOE", "DICOM", "EHR", "FHIR", "HIE", "HL7",
    "ML", "NLP", "PHI", "PII", "RCT", "ROC", "SQL",
    
    # Organizations and Standards
    "ACGME", "AMA", "CDC", "CMS", "FDA", "HIPAA", "JCAHO", "NIH", "WHO"
]

# Acronyms that should be pronounced as words (exceptions)
WORD_ACRONYMS = [
    "AIDS", "CABG", "COVID", "ELISA", "GERD", "LASER", "NASA", "NOAEL",
    "RAST", "SOAP", "TURP", "UNESCO"
]

class WordReplacer:
    def __init__(self, replacements=tts_replacements):
        # Create a dictionary of replacements
        self.replacements = replacements
        
        # Sort keys by length (longest first) to handle overlapping patterns
        self.sorted_keys = sorted(self.replacements.keys(), key=len, reverse=True)
    
    def replace(self, text):
        # Simple direct replacement (more reliable than regex for this case)
        result = text
        for key in self.sorted_keys:
            result = result.replace(key, self.replacements[key])
        return result

# Create a single global instance
word_replacer = WordReplacer()

def markdown_to_speech(text):
    """
    Convert markdown text to speech-friendly text by:
    - Replacing hyperlinks with "link provided" or "links provided"
    - Replacing image links with "image provided" 
    - Removing formatting characters and other elements that would disrupt speech flow
    - Suppressing alternate text
    - Separating medical acronyms with spaces for better TTS pronunciation
    - Replacing common abbreviations with their full forms
    
    Args:
        text (str): Markdown text to convert
        
    Returns:
        str: Text suitable for TTS systems
    """
    # Replace image markdown with "image provided"
    text = IMAGE_PATTERN.sub(" image provided ", text)
    text = INLINE_IMAGE_PATTERN.sub(" image provided ", text)
    
    # Replace consecutive links with "links provided"
    text = CONSECUTIVE_LINKS_PATTERN.sub(" links provided ", text)
    
    # Replace single links with "link provided"
    text = SINGLE_LINK_PATTERN.sub(" link provided ", text)
    
    # Remove code blocks and inline code
    text = CODE_BLOCK_PATTERN.sub("", text)
    text = INLINE_CODE_PATTERN.sub("", text)
    
    # Remove headers
    text = HEADER_PATTERN.sub("", text)
    
    # Remove bold and italic formatting
    text = BOLD_ASTERISK_PATTERN.sub(r'\1', text)
    text = BOLD_UNDERSCORE_PATTERN.sub(r'\1', text)
    text = ITALIC_ASTERISK_PATTERN.sub(r'\1', text)
    text = ITALIC_UNDERSCORE_PATTERN.sub(r'\1', text)
    
    # Remove blockquotes
    text = BLOCKQUOTE_PATTERN.sub("", text)
    
    # Remove HTML tags
    text = HTML_TAG_PATTERN.sub("", text)
    
    # Remove bullet points and numbered lists
    text = BULLET_LIST_PATTERN.sub("", text)
    text = NUMBERED_LIST_PATTERN.sub("", text)
    
    # Remove horizontal rules
    text = HORIZONTAL_RULE_PATTERN.sub("", text)
    
    # Remove table formatting
    text = TABLE_PATTERN.sub("", text)
    text = TABLE_SEPARATOR_PATTERN.sub("", text)
    
    # Fix missing spaces between words (like "organizationbut")
    text = WORD_BOUNDARY_PATTERN.sub(r'\1 \2', text)
    
    # Replace common abbreviations with their full forms
    # Switched from regex to direct string replacement which is more reliable
    text = word_replacer.replace(text)
    
    # Handle specific medical acronyms - add spaces between letters
    for acronym in MEDICAL_ACRONYMS:
        pattern = re.compile(r'\b' + re.escape(acronym) + r'\b')
        text = pattern.sub(' '.join(acronym), text)
    
    # Catch other potential acronyms (uppercase sequences of 2+ letters)
    # but skip those in the WORD_ACRONYMS list
    def process_acronym(match):
        matched_text = match.group(0)
        if matched_text in WORD_ACRONYMS:
            return matched_text  # Keep as is
        return ' '.join(matched_text)  # Add spaces between letters
    
    # Find uppercase sequences not in our exceptions list
    other_acronyms_pattern = re.compile(r'\b[A-Z]{2,}\b')
    text = other_acronyms_pattern.sub(process_acronym, text)
    text = URL_PATTERN.sub(" link provided ", text)
    
    # Remove excessive whitespace
    text = WHITESPACE_PATTERN.sub(" ", text)
    
    # Remove escaped characters
    text = ESCAPED_CHAR_PATTERN.sub(r'\1', text)
    
    return text.strip()

# Example usage
if __name__ == "__main__":
    # Test with a more complex example
    complex_md_text = """
    # Header
    This is a **bold** statement and this is _italic_.
    ![Image](http://example.com/image.png) and [Link](http://example.com).
    ## Subheader
    - Bullet point 1
    - Bullet point 2
    1. Numbered point 1
    2. Numbered point 2
    > This is a blockquote.
    ```python
    def example():
        pass
    ```
    The RACGP is a great organization but WHO is greater
    Dr. Smith is a great doctor. I.e. he is the best.
    The URL for the Royal Australian College of General Practitioners (RACGP) is https://www.racgp.org.au/. "
    """
    
    print("Original text:")
    print(complex_md_text)
    print("Converted text:")
    print(markdown_to_speech(complex_md_text))  # Should handle all formatting and links
    