# Code Graph - Codebase Ingestion and Parsing
# This module handles repository cloning and local file reading

import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional, Tuple, List
from git import Repo, GitCommandError

# Import utilities
from .utilities import (
    # File utilities
    format_file_size,
    get_directory_size,
    is_likely_binary,
    read_file_content,
    should_exclude_file,
    has_valid_extension,
    
    # Folder utilities
    get_folder_statistics,
    list_cloned_repositories,
    cleanup_cloned_repositories,
    
    # Git utilities
    is_valid_repo_url,
    extract_repo_name,
    get_repository_info
)


def detect_language_from_extension(extension: str) -> str:
    """
    Detect programming language from file extension
    
    Args:
        extension: File extension (e.g., '.py', '.java')
        
    Returns:
        str: Programming language name
    """
    extension = extension.lower().lstrip('.')
    
    language_map = {
        'py': 'python',
        'java': 'java',
        'js': 'javascript',
        'jsx': 'javascript',
        'ts': 'typescript',
        'tsx': 'typescript',
        'cpp': 'cpp',
        'cc': 'cpp',
        'cxx': 'cpp',
        'c': 'c',
        'h': 'c',
        'hpp': 'cpp',
        'cs': 'csharp',
        'rb': 'ruby',
        'go': 'go',
        'rs': 'rust',
        'php': 'php',
        'swift': 'swift',
        'kt': 'kotlin',
        'scala': 'scala',
        'r': 'r',
        'sql': 'sql',
        'sh': 'shell',
        'bash': 'shell',
        'zsh': 'shell',
        'ps1': 'powershell',
        'html': 'html',
        'css': 'css',
        'scss': 'scss',
        'sass': 'sass',
        'xml': 'xml',
        'json': 'json',
        'yaml': 'yaml',
        'yml': 'yaml',
        'md': 'markdown',
        'dockerfile': 'dockerfile'
    }
    
    return language_map.get(extension, 'unknown')


def clone_repository(repo_url: str, target_dir: Optional[str] = None, use_project_dir: bool = True) -> Tuple[bool, str, Optional[str]]:
    """
    Clone a GitHub/Bitbucket repository to a target directory
    
    Args:
        repo_url: URL of the repository to clone (supports HTTP/HTTPS/SSH)
        target_dir: Directory to clone the repository into (optional)
        use_project_dir: If True, use project's cloned_repos directory (default: True)
        
    Returns:
        Tuple[bool, str, Optional[str]]: (success, message, cloned_path)
            - success: True if cloning was successful, False otherwise
            - message: Success/error message
            - cloned_path: Path to the cloned repository (None if failed)
    """
    try:
        # Validate the repository URL
        if not is_valid_repo_url(repo_url):
            return False, f"Invalid repository URL: {repo_url}", None
        
        # Determine target directory
        if target_dir is None:
            if use_project_dir:
                # Use project's cloned_repos directory
                project_root = Path(__file__).parent.parent  # Go up from app/ to project root
                target_dir = project_root / "cloned_repos"
                target_dir.mkdir(exist_ok=True)
                target_dir = str(target_dir)
            else:
                # Use temporary directory
                target_dir = tempfile.mkdtemp(prefix="code_graph_repo_")
        else:
            # Ensure target directory exists
            Path(target_dir).mkdir(parents=True, exist_ok=True)
        
        # Extract repository name for the clone directory
        repo_name = extract_repo_name(repo_url)
        clone_path = os.path.join(target_dir, repo_name)
        
        # Remove existing directory if it exists
        if os.path.exists(clone_path):
            print(f"🗑️ Removing existing directory: {clone_path}")
            shutil.rmtree(clone_path)
        
        print(f"🔄 Cloning repository from {repo_url}...")
        print(f"📁 Target directory: {clone_path}")
        
        # Clone the repository
        repo = Repo.clone_from(
            url=repo_url,
            to_path=clone_path,
            depth=1,  # Shallow clone for faster download
            single_branch=True  # Only clone the default branch
        )
        
        # Verify the clone was successful
        if not repo.git_dir:
            return False, "Repository cloning failed - no git directory found", None
        
        # Get repository information
        repo_info = get_repository_info(repo)
        
        success_msg = (
            f"✅ Repository cloned successfully!\n"
            f"📍 Location: {clone_path}\n"
            f"🌿 Branch: {repo_info['branch']}\n"
            f"📝 Latest commit: {repo_info['latest_commit'][:8]}\n"
            f"👤 Author: {repo_info['author']}\n"
            f"📊 Repository size: {get_directory_size(clone_path)}"
        )
        
        return True, success_msg, clone_path
        
    except GitCommandError as e:
        error_msg = f"Git command failed: {str(e)}"
        if "Authentication failed" in str(e):
            error_msg += "\n💡 Tip: Make sure the repository is public or you have proper authentication set up."
        elif "Repository not found" in str(e):
            error_msg += "\n💡 Tip: Check if the repository URL is correct and the repository exists."
        return False, error_msg, None
        
    except Exception as e:
        return False, f"Unexpected error during cloning: {str(e)}", None


def read_local_folder(folder_path: str) -> Tuple[bool, str, Optional[str]]:
    """
    Validate and prepare a local folder for code processing
    
    Args:
        folder_path: Path to the local folder containing code
        
    Returns:
        Tuple[bool, str, Optional[str]]: (success, message, validated_path)
            - success: True if folder is valid, False otherwise
            - message: Success/error message
            - validated_path: Absolute path to the folder (None if failed)
    """
    try:
        folder_path = Path(folder_path).resolve()
        
        # Validate folder exists
        if not folder_path.exists():
            return False, f"Folder does not exist: {folder_path}", None
        
        if not folder_path.is_dir():
            return False, f"Path is not a directory: {folder_path}", None
        
        # Check if folder is accessible
        try:
            list(folder_path.iterdir())
        except PermissionError:
            return False, f"Permission denied accessing folder: {folder_path}", None
        
        # Get basic folder statistics for user information
        stats = get_folder_statistics(str(folder_path))
        
        success_message = (
            f"✅ Local folder validated successfully!\n"
            f"📍 Location: {folder_path}\n"
            f"📊 Total files: {stats.get('total_files', 'Unknown')}\n"
            f"📂 Total directories: {stats.get('total_directories', 'Unknown')}\n"
            f"💾 Total size: {stats.get('total_size_human', 'Unknown')}\n"
            f"🗂️ File extensions found: {len(stats.get('file_extensions', {}))}"
        )
        
        return True, success_message, str(folder_path)
        
    except Exception as e:
        return False, f"Error validating local folder: {str(e)}", None


def discover_code_files(codebase_path: str, include_extensions: Optional[list] = None, exclude_patterns: Optional[list] = None, max_file_size_mb: int = 10) -> Tuple[bool, str, list]:
    """
    Discover and read code files from a codebase directory
    This function is used by parse_code_chunks() to process files
    
    Args:
        codebase_path: Path to the codebase directory
        include_extensions: List of file extensions to include (e.g., ['.py', '.js', '.java'])
                          If None, uses default code extensions
        exclude_patterns: List of patterns to exclude (e.g., ['__pycache__', '.git', 'node_modules'])
                         If None, uses default exclude patterns
        max_file_size_mb: Maximum file size in MB to process (default: 10MB)
        
    Returns:
        Tuple[bool, str, list]: (success, message, file_data_list)
            - success: True if discovery was successful, False otherwise
            - message: Success/error message
            - file_data_list: List of dictionaries with file information
    """
    try:
        codebase_path = Path(codebase_path).resolve()
        
        # Validate path exists
        if not codebase_path.exists() or not codebase_path.is_dir():
            return False, f"Invalid codebase path: {codebase_path}", []
        
        # Default code file extensions
        if include_extensions is None:
            include_extensions = [
                # Python
                '.py', '.pyx', '.pyi',
                # JavaScript/TypeScript
                '.js', '.jsx', '.ts', '.tsx', '.mjs',
                # Java
                '.java', '.kt', '.scala',
                # C/C++
                '.c', '.cpp', '.cc', '.cxx', '.h', '.hpp', '.hxx',
                # C#
                '.cs', '.vb',
                # Go
                '.go',
                # Rust
                '.rs',
                # PHP
                '.php', '.phtml',
                # Ruby
                '.rb', '.rbw',
                # Swift
                '.swift',
                # Dart
                '.dart',
                # R
                '.r', '.R',
                # Shell
                '.sh', '.bash', '.zsh', '.fish',
                # Web
                '.html', '.htm', '.css', '.scss', '.sass', '.less',
                # Config/Data
                '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg',
                '.xml', '.sql', '.md', '.rst', '.txt',
                # Build files
                '.gradle', '.maven', '.cmake', '.make', 'Makefile', 'Dockerfile',
                # Other
                '.pl', '.lua', '.vim', '.el'
            ]
        
        # Default exclude patterns
        if exclude_patterns is None:
            exclude_patterns = [
                # Version control
                '.git', '.svn', '.hg', '.bzr',
                # Dependencies
                'node_modules', '__pycache__', '.pytest_cache',
                'venv', 'env', '.env', 'virtualenv',
                'target', 'build', 'dist', '.gradle',
                'vendor', 'Pods', 'packages',
                # IDE/Editor
                '.vscode', '.idea', '.eclipse', '.settings',
                '.vs', '*.swp', '*.swo', '*~',
                # OS
                '.DS_Store', 'Thumbs.db', 'desktop.ini',
                # Logs and temp
                '*.log', '*.tmp', '*.temp', 'logs',
                # Compiled/Binary
                '*.pyc', '*.pyo', '*.class', '*.o', '*.so', '*.dll', '*.exe',
                '*.jar', '*.war', '*.ear', '*.zip', '*.tar', '*.gz',
                # Media
                '*.jpg', '*.jpeg', '*.png', '*.gif', '*.svg', '*.ico',
                '*.mp3', '*.mp4', '*.avi', '*.mov', '*.pdf'
            ]
        
        print(f"🔍 Discovering code files in: {codebase_path}")
        print(f"📝 Looking for extensions: {', '.join(include_extensions[:10])}{'...' if len(include_extensions) > 10 else ''}")
        
        file_data_list = []
        total_files_found = 0
        total_files_processed = 0
        total_size_bytes = 0
        max_file_size_bytes = max_file_size_mb * 1024 * 1024
        
        # Walk through all files in the directory
        for file_path in codebase_path.rglob('*'):
            if file_path.is_file():
                total_files_found += 1
                
                # Check if file should be excluded
                if should_exclude_file(file_path, codebase_path, exclude_patterns):
                    continue
                
                # Check file extension
                if not has_valid_extension(file_path, include_extensions):
                    continue
                
                # Check file size
                try:
                    file_size = file_path.stat().st_size
                    if file_size > max_file_size_bytes:
                        print(f"⚠️ Skipping large file: {file_path.name} ({file_size / (1024*1024):.1f}MB)")
                        continue
                    
                    total_size_bytes += file_size
                except OSError:
                    continue
                
                # Read file content
                try:
                    file_content = read_file_content(file_path)
                    if file_content is None:
                        continue
                    
                    # Create file data dictionary
                    relative_path = file_path.relative_to(codebase_path)
                    file_data = {
                        'name': file_path.name,
                        'path': str(file_path),
                        'relative_path': str(relative_path),
                        'extension': file_path.suffix.lower(),
                        'size_bytes': file_size,
                        'size_human': format_file_size(file_size),
                        'content': file_content,
                        'lines': len(file_content.splitlines()),
                        'modified_time': file_path.stat().st_mtime,
                        'is_binary': is_likely_binary(file_content)
                    }
                    
                    file_data_list.append(file_data)
                    total_files_processed += 1
                    
                except Exception as e:
                    print(f"⚠️ Error reading file {file_path}: {e}")
                    continue
        
        # Sort files by relative path for consistent ordering
        file_data_list.sort(key=lambda x: x['relative_path'])
        
        success_message = (
            f"✅ Successfully discovered code files!\n"
            f"📍 Location: {codebase_path}\n"
            f"📊 Files found: {total_files_found}\n"
            f"📝 Files processed: {total_files_processed}\n"
            f"💾 Total size: {format_file_size(total_size_bytes)}\n"
            f"🗂️ File types: {', '.join(sorted(set(f['extension'] for f in file_data_list if f['extension'])))}"
        )
        
        return True, success_message, file_data_list
        
    except Exception as e:
        return False, f"Error discovering code files: {str(e)}", []


def parse_code_chunks(codebase_path: str, chunk_size: int = 500, chunk_overlap: int = 50, include_extensions: Optional[list] = None, exclude_patterns: Optional[list] = None) -> Tuple[bool, str, list]:
    """
    Parse code into chunks for processing using LangChain
    
    Args:
        codebase_path: Path to the codebase directory (from clone_repository or read_local_folder)
        chunk_size: Maximum size of each chunk in characters (default: 500)
        chunk_overlap: Number of characters to overlap between chunks (default: 50)
        include_extensions: List of file extensions to include (optional, uses defaults if None)
        exclude_patterns: List of patterns to exclude (optional, uses defaults if None)
        
    Returns:
        Tuple[bool, str, list]: (success, message, chunked_documents)
            - success: True if chunking was successful, False otherwise
            - message: Success/error message
            - chunked_documents: List of LangChain Document objects with chunks
    """
    try:
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        from langchain.schema import Document
        
        print(f"📝 Parsing code chunks from: {codebase_path}")
        print(f"⚙️ Chunk size: {chunk_size}, Overlap: {chunk_overlap}")
        
        # Step 1: Discover code files
        success, discovery_message, file_data_list = discover_code_files(
            codebase_path, 
            include_extensions=include_extensions,
            exclude_patterns=exclude_patterns
        )
        
        if not success:
            return False, f"Failed to discover code files: {discovery_message}", []
        
        if not file_data_list:
            return False, "No code files found in the codebase", []
        
        print(f"📁 Found {len(file_data_list)} code files to process")
        
        # Step 2: Create LangChain Documents from file data
        documents = []
        total_content_size = 0
        
        for file_data in file_data_list:
            # Create metadata for the document
            metadata = {
                'source': file_data['path'],
                'filename': file_data['name'],
                'relative_path': file_data['relative_path'],
                'file_extension': file_data['extension'],
                'file_size_bytes': file_data['size_bytes'],
                'file_size_human': file_data['size_human'],
                'lines': file_data['lines'],
                'modified_time': file_data['modified_time'],
                'is_binary': file_data['is_binary']
            }
            
            # Create LangChain Document
            document = Document(
                page_content=file_data['content'],
                metadata=metadata
            )
            
            documents.append(document)
            total_content_size += len(file_data['content'])
        
        print(f"📄 Created {len(documents)} documents ({format_file_size(total_content_size)} total content)")
        
        # Step 3: Set up text splitter for code
        # Use language-specific separators for better code chunking
        code_separators = [
            # Python
            "\nclass ", "\ndef ", "\n\ndef ", "\n\nclass ",
            # Java/C++/JavaScript
            "\npublic class ", "\nprivate class ", "\nprotected class ",
            "\npublic ", "\nprivate ", "\nprotected ",
            "\nfunction ", "\n\nfunction ",
            # General code patterns
            "\n\n", "\n", " ", ""
        ]
        
        text_splitter = RecursiveCharacterTextSplitter(
            separators=code_separators,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            is_separator_regex=False,
        )
        
        # Step 4: Split documents into chunks
        print(f"✂️ Splitting documents into chunks...")
        chunked_documents = text_splitter.split_documents(documents)
        
        # Step 5: Add chunk-specific metadata
        for i, chunk in enumerate(chunked_documents):
            chunk.metadata['chunk_id'] = i
            chunk.metadata['chunk_size'] = len(chunk.page_content)
            chunk.metadata['codebase_path'] = codebase_path
            
            # Fix metadata key mismatch - standardize to what graph_builder expects
            chunk.metadata['file_path'] = chunk.metadata.get('source', 'unknown')
            chunk.metadata['language'] = detect_language_from_extension(chunk.metadata.get('file_extension', ''))
            
            # Add line number tracking for chunks (approximate)
            content_lines = chunk.page_content.split('\n')
            chunk.metadata['start_line'] = 1  # Will be improved with better chunking
            chunk.metadata['end_line'] = len(content_lines)
        
        # Calculate statistics
        total_chunks = len(chunked_documents)
        avg_chunk_size = sum(len(chunk.page_content) for chunk in chunked_documents) / total_chunks if total_chunks > 0 else 0
        
        success_message = (
            f"✅ Successfully parsed code into chunks!\n"
            f"📍 Codebase: {codebase_path}\n"
            f"📁 Files processed: {len(file_data_list)}\n"
            f"📄 Documents created: {len(documents)}\n"
            f"✂️ Total chunks: {total_chunks}\n"
            f"📏 Average chunk size: {avg_chunk_size:.0f} characters\n"
            f"💾 Total content: {format_file_size(total_content_size)}"
        )
        
        return True, success_message, chunked_documents
        
    except ImportError as e:
        return False, f"Missing required dependency: {str(e)}. Please install langchain.", []
    except Exception as e:
        return False, f"Error parsing code chunks: {str(e)}", [] 