# Code Graph - File Utilities
# File-related utility functions

import os
from pathlib import Path
from typing import Optional


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        str: Human-readable size
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def get_directory_size(directory_path: str) -> str:
    """
    Get human-readable size of a directory
    
    Args:
        directory_path: Path to the directory
        
    Returns:
        str: Human-readable size (e.g., "2.5 MB")
    """
    try:
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(directory_path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    total_size += os.path.getsize(filepath)
        
        return format_file_size(total_size)
        
    except Exception:
        return "Unknown size"


def is_likely_binary(content: str) -> bool:
    """
    Check if content is likely binary (contains non-printable characters)
    
    Args:
        content: File content string
        
    Returns:
        bool: True if likely binary, False otherwise
    """
    try:
        # Check for null bytes (common in binary files)
        if '\x00' in content:
            return True
        
        # Check ratio of printable characters
        printable_chars = sum(1 for c in content if c.isprintable() or c.isspace())
        total_chars = len(content)
        
        if total_chars == 0:
            return False
        
        printable_ratio = printable_chars / total_chars
        return printable_ratio < 0.7  # If less than 70% printable, likely binary
        
    except Exception:
        return True


def read_file_content(file_path: Path) -> Optional[str]:
    """
    Read file content with proper encoding detection
    
    Args:
        file_path: Path to the file
        
    Returns:
        Optional[str]: File content or None if failed
    """
    encodings_to_try = ['utf-8', 'utf-16', 'latin-1', 'cp1252']
    
    for encoding in encodings_to_try:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
                # Basic check if content is readable
                if len(content.strip()) == 0 and file_path.stat().st_size > 0:
                    continue  # Likely wrong encoding
                return content
        except (UnicodeDecodeError, UnicodeError):
            continue
        except Exception:
            break
    
    return None


def should_exclude_file(file_path: Path, base_path: Path, exclude_patterns: list) -> bool:
    """
    Check if a file should be excluded based on exclude patterns
    
    Args:
        file_path: Path to the file
        base_path: Base directory path
        exclude_patterns: List of patterns to exclude
        
    Returns:
        bool: True if file should be excluded, False otherwise
    """
    try:
        # Get relative path for pattern matching
        relative_path = file_path.relative_to(base_path)
        path_parts = relative_path.parts
        file_name = file_path.name
        
        for pattern in exclude_patterns:
            # Check if pattern matches any part of the path
            if any(pattern in part for part in path_parts):
                return True
            
            # Check if pattern matches the filename
            if pattern in file_name:
                return True
            
            # Check for wildcard patterns
            if pattern.startswith('*.') and file_name.endswith(pattern[1:]):
                return True
        
        return False
        
    except Exception:
        return True  # Exclude if we can't determine


def has_valid_extension(file_path: Path, include_extensions: list) -> bool:
    """
    Check if a file has a valid extension
    
    Args:
        file_path: Path to the file
        include_extensions: List of valid extensions
        
    Returns:
        bool: True if file has valid extension, False otherwise
    """
    file_extension = file_path.suffix.lower()
    file_name = file_path.name
    
    # Check extension
    if file_extension in include_extensions:
        return True
    
    # Check for files without extensions (like Makefile, Dockerfile)
    if file_name in include_extensions:
        return True
    
    return False 