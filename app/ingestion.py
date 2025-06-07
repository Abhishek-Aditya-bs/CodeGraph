# Code Graph - Codebase Ingestion and Parsing
# This module handles repository cloning and local file reading

import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urlparse
import git
from git import Repo, GitCommandError, InvalidGitRepositoryError


def clone_repository(repo_url: str, target_dir: Optional[str] = None) -> Tuple[bool, str, Optional[str]]:
    """
    Clone a GitHub/Bitbucket repository to a target directory
    
    Args:
        repo_url: URL of the repository to clone (supports HTTP/HTTPS/SSH)
        target_dir: Directory to clone the repository into (optional, creates temp dir if None)
        
    Returns:
        Tuple[bool, str, Optional[str]]: (success, message, cloned_path)
            - success: True if cloning was successful, False otherwise
            - message: Success/error message
            - cloned_path: Path to the cloned repository (None if failed)
    """
    try:
        # Validate the repository URL
        if not _is_valid_repo_url(repo_url):
            return False, f"Invalid repository URL: {repo_url}", None
        
        # Create target directory if not provided
        if target_dir is None:
            target_dir = tempfile.mkdtemp(prefix="code_graph_repo_")
        else:
            # Ensure target directory exists
            Path(target_dir).mkdir(parents=True, exist_ok=True)
        
        # Extract repository name for the clone directory
        repo_name = _extract_repo_name(repo_url)
        clone_path = os.path.join(target_dir, repo_name)
        
        # Remove existing directory if it exists
        if os.path.exists(clone_path):
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
        repo_info = _get_repository_info(repo)
        
        success_msg = (
            f"✅ Repository cloned successfully!\n"
            f"📍 Location: {clone_path}\n"
            f"🌿 Branch: {repo_info['branch']}\n"
            f"📝 Latest commit: {repo_info['latest_commit'][:8]}\n"
            f"👤 Author: {repo_info['author']}"
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


def _is_valid_repo_url(url: str) -> bool:
    """
    Validate if the URL is a valid Git repository URL
    
    Args:
        url: Repository URL to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        parsed = urlparse(url)
        
        # Check if it's a valid URL
        if not parsed.scheme or not parsed.netloc:
            return False
        
        # Support common Git hosting services
        valid_hosts = [
            'github.com', 'gitlab.com', 'bitbucket.org',
            'git.sr.ht', 'codeberg.org', 'gitea.com'
        ]
        
        # Check for SSH URLs (git@host:user/repo.git)
        if url.startswith('git@'):
            return True
        
        # Check for HTTPS/HTTP URLs
        if parsed.scheme in ['http', 'https']:
            # Check if it's from a known Git hosting service
            if any(host in parsed.netloc for host in valid_hosts):
                return True
            # Or if it ends with .git
            if url.endswith('.git'):
                return True
        
        return False
        
    except Exception:
        return False


def _extract_repo_name(repo_url: str) -> str:
    """
    Extract repository name from URL
    
    Args:
        repo_url: Repository URL
        
    Returns:
        str: Repository name
    """
    try:
        # Handle SSH URLs (git@github.com:user/repo.git)
        if repo_url.startswith('git@'):
            repo_name = repo_url.split(':')[-1]
        else:
            # Handle HTTPS URLs
            repo_name = repo_url.split('/')[-1]
        
        # Remove .git extension if present
        if repo_name.endswith('.git'):
            repo_name = repo_name[:-4]
        
        return repo_name
        
    except Exception:
        return "unknown_repo"


def _get_repository_info(repo: Repo) -> dict:
    """
    Get basic information about the cloned repository
    
    Args:
        repo: GitPython Repo object
        
    Returns:
        dict: Repository information
    """
    try:
        latest_commit = repo.head.commit
        return {
            'branch': repo.active_branch.name,
            'latest_commit': latest_commit.hexsha,
            'author': latest_commit.author.name,
            'commit_date': latest_commit.committed_datetime.isoformat(),
            'commit_message': latest_commit.message.strip()
        }
    except Exception:
        return {
            'branch': 'unknown',
            'latest_commit': 'unknown',
            'author': 'unknown',
            'commit_date': 'unknown',
            'commit_message': 'unknown'
        }


def test_repository_cloning(test_repo_url: str = "https://github.com/octocat/Hello-World.git") -> bool:
    """
    Test the repository cloning functionality with a public repository
    
    Args:
        test_repo_url: URL of a public repository to test with
        
    Returns:
        bool: True if test passed, False otherwise
    """
    print(f"🧪 Testing repository cloning with: {test_repo_url}")
    
    success, message, cloned_path = clone_repository(test_repo_url)
    
    print(f"📊 Test Result: {'PASSED' if success else 'FAILED'}")
    print(f"📝 Message: {message}")
    
    if success and cloned_path:
        # Verify some basic files exist
        files_found = list(Path(cloned_path).rglob("*"))[:5]  # First 5 files
        print(f"📁 Files found: {len(files_found)} (showing first 5)")
        for file_path in files_found:
            if file_path.is_file():
                print(f"   - {file_path.name}")
        
        # Clean up test directory
        try:
            shutil.rmtree(cloned_path)
            print("🧹 Test directory cleaned up")
        except Exception as e:
            print(f"⚠️ Warning: Could not clean up test directory: {e}")
    
    return success


def read_local_folder(folder_path: str) -> list:
    """
    Read code files from a local folder
    
    Args:
        folder_path: Path to the local folder containing code
        
    Returns:
        list: List of file paths and contents
    """
    # TODO: Implement local folder reading
    pass

def parse_code_chunks(documents: list) -> list:
    """
    Parse code into chunks for processing
    
    Args:
        documents: List of document objects
        
    Returns:
        list: List of chunked Document objects
    """
    # TODO: Implement code chunking using LangChain
    pass 