import pdfplumber
import json
import aiohttp
import asyncio
import re
from pathlib import Path
from typing import Optional, List, Tuple
from app.core.config import settings

class PDFService:
    @staticmethod
    async def extract_text(file_path: Path) -> str:
        """Extract text from PDF file."""
        text = ""
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ""
            return text
        except Exception as e:
            raise ValueError(f"Failed to extract text from PDF: {str(e)}")

    @staticmethod
    async def extract_github_username(text: str) -> Optional[str]:
        """Extract GitHub organization username using regex patterns."""
        # Common patterns for GitHub organization mentions
        patterns = [
            r'github\.com/([a-zA-Z0-9-]+)(?:/|$)',  # matches github.com/org
            r'github\.com/orgs/([a-zA-Z0-9-]+)(?:/|$)',  # matches github.com/orgs/org
            r'@([a-zA-Z0-9-]+) on GitHub',  # matches @org on GitHub
            r'GitHub organization .*?[/@]([a-zA-Z0-9-]+)',  # matches GitHub organization blah/org
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                username = match.group(1)
                if username and username.lower() not in ['github', 'http', 'https']:
                    return username
        
        return None

    @staticmethod
    async def fetch_github_members(org_username: str) -> List[str]:
        """Fetch public members of a GitHub organization."""
        headers = {}
        if settings.GITHUB_TOKEN:
            headers["Authorization"] = f"token {settings.GITHUB_TOKEN}"

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://api.github.com/orgs/{org_username}/public_members",
                headers=headers
            ) as response:
                if response.status == 404:
                    return []
                elif response.status == 200:
                    members = await response.json()
                    return [member["login"] for member in members]
                else:
                    response.raise_for_status()

    @staticmethod
    async def process_pdf(file_path: Path) -> Tuple[Optional[str], List[str]]:
        """Process PDF file and return extracted GitHub org and members."""
        text = await PDFService.extract_text(file_path)
        org_username = await PDFService.extract_github_username(text)
        
        if org_username:
            members = await PDFService.fetch_github_members(org_username)
            return org_username, members
        
        return None, [] 