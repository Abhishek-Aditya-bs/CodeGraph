# Code Graph - Configuration and Environment Variables
# This module handles loading and managing environment variables

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class for Code Graph application"""
    
    # Neo4j Configuration
    NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
    NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Application Configuration
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o")
    
    @classmethod
    def validate_config(cls) -> bool:
        """
        Validate that all required configuration is present
        
        Returns:
            bool: True if all required config is present, False otherwise
        """
        required_vars = [
            cls.OPENAI_API_KEY,
            cls.NEO4J_URI,
            cls.NEO4J_USERNAME,
            cls.NEO4J_PASSWORD
        ]
        
        missing_vars = [var for var in required_vars if not var]
        
        if missing_vars:
            print(f"Missing required environment variables: {missing_vars}")
            return False
        
        return True

# Create a global config instance
config = Config() 