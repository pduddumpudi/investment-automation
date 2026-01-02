"""
Configuration management for the investment automation tool.
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Centralized configuration management."""

    def __init__(self):
        self.base_dir = Path(__file__).parent.parent.parent
        self.config_dir = self.base_dir / 'config'
        self.data_dir = self.base_dir / 'data'
        self.docs_dir = self.base_dir / 'docs'

        # API Keys (optional)
        self.openai_api_key = os.getenv('OPENAI_API_KEY')  # For LLM-based ticker extraction

        # Ensure directories exist
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.docs_dir.mkdir(parents=True, exist_ok=True)

    def load_json(self, filename: str) -> Dict[str, Any]:
        """Load a JSON configuration file."""
        file_path = self.config_dir / filename
        if not file_path.exists():
            return {}

        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_json(self, filename: str, data: Dict[str, Any]) -> None:
        """Save data to a JSON configuration file."""
        file_path = self.config_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get_dataroma_investors(self) -> List[str]:
        """Get list of Dataroma investors to track."""
        data = self.load_json('dataroma_investors.json')
        return data.get('investors', [])

    def get_substack_publications(self) -> List[Dict[str, str]]:
        """Get list of Substack publications."""
        data = self.load_json('substack_publications.json')
        return data.get('publications', [])

    def save_substack_publications(self, publications: List[Dict[str, str]]) -> None:
        """Save Substack publications list."""
        self.save_json('substack_publications.json', {'publications': publications})


# Global config instance
config = Config()
