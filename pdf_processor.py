import re
import requests
from pathlib import Path
from typing import Optional, List, Tuple
import pdfplumber

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF file."""
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text
    except Exception as e:
        raise ValueError(f"Failed to extract text from PDF: {str(e)}")

def extract_github_org(text: str) -> Optional[str]:
    """Extract GitHub organization from text using regex patterns."""
    # Common patterns for GitHub organization mentions
    patterns = [
        r'github\.com/([a-zA-Z0-9-_]+)(?:/|$|\s)',  # github.com/org
        r'github\.com/orgs/([a-zA-Z0-9-_]+)(?:/|$|\s)',  # github.com/orgs/org
        r'@([a-zA-Z0-9-_]+)\s+on\s+GitHub',  # @org on GitHub
        r'GitHub\s+organization[:\s]+([a-zA-Z0-9-_]+)',  # GitHub organization: org
        r'GitHub\s+org[:\s]+([a-zA-Z0-9-_]+)',  # GitHub org: org
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            org = match.group(1)
            # Filter out common false positives
            if org and org.lower() not in ['github', 'http', 'https', 'www', 'com']:
                return org
    
    return None

def fetch_github_members(org_name: str) -> List[str]:
    """Fetch public members of a GitHub organization."""
    url = f"https://api.github.com/orgs/{org_name}/public_members"
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 404:
            # Organization not found or no public members
            return []
        
        if response.status_code == 200:
            members_data = response.json()
            return [member['login'] for member in members_data]
        
        # Handle rate limiting or other errors
        response.raise_for_status()
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching GitHub members: {e}")
        return []
    
    return []

def process_pdf_file(file_path: str) -> Tuple[Optional[str], List[str]]:
    """
    Main function to process PDF file and extract GitHub organization info.
    
    Returns:
        Tuple of (organization_name, list_of_members)
    """
    # Extract text from PDF
    text = extract_text_from_pdf(file_path)
    
    if not text.strip():
        raise ValueError("No text could be extracted from the PDF")
    
    # Extract GitHub organization
    org_name = extract_github_org(text)
    
    if not org_name:
        return None, []
    
    # Fetch organization members
    members = fetch_github_members(org_name)
    
    return org_name, members 