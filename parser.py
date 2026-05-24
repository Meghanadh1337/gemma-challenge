import pdfplumber
import io
import re
from typing import List

def sanitize_text(text: str) -> str:
    """
    Cleans extracted text by removing excessive whitespace and non-readable artifacts.
    """
    # Remove non-ascii characters that often clutter PDF extractions
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    # Collapse multiple spaces and newlines
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def forensic_pruning(full_text: str) -> str:
    """
    Surgically extracts the highest-signal sections while maintaining forensic integrity.
    """
    targets = {
        "Risk Factors": r"ITEM\s+1A",
        "MD&A": r"ITEM\s+7",
        "Financials": r"ITEM\s+8",
        "Controls": r"ITEM\s+9A"
    }
    
    pruned_content = ""
    for name, pattern in targets.items():
        match = re.search(pattern, full_text, re.IGNORECASE)
        if match:
            # Take a 25,000 character window (cleaner text allows for more signal)
            start = match.start()
            content = sanitize_text(full_text[start : start + 30000])
            pruned_content += f"\n--- {name.upper()} ---\n{content}\n"
            
    return pruned_content if pruned_content else sanitize_text(full_text)[:100000]

def parse_pdfs(pdf_files: List[bytes]) -> str:
    """
    Parses multiple PDF files from bytes and concatenates their text content.
    Applies forensic pruning if the content exceeds the 128K context window.
    """
    concatenated_text = []
    
    for pdf_bytes in pdf_files:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    concatenated_text.append(text)
    
    full_text = "\n\n".join(concatenated_text)
    
    # Handle context window limits
    if len(full_text) > 128000:
        print(f"Warning: Extracted text length ({len(full_text)}) exceeds 128K characters. Pruning for signal...")
        return forensic_pruning(full_text)
        
    return full_text
