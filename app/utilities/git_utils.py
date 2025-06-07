# Code Graph - Git Utilities
# Git-related utility functions

from urllib.parse import urlparse
from git import Repo


def is_valid_repo_url(url: str) -> bool:
    """
    Validate if the URL is a valid Git repository URL
    
    Args:
        url: Repository URL to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        # Check for SSH URLs (git@host:user/repo.git)
        if url.startswith('git@'):
            # SSH URL format: git@hostname:username/repository.git
            if ':' in url and '/' in url.split(':')[-1]:
                return True
            return False
        
        # Parse HTTP/HTTPS URLs
        parsed = urlparse(url)
        
        # Check if it's a valid URL
        if not parsed.scheme or not parsed.netloc:
            return False
        
        # Support common Git hosting services
        valid_hosts = [
            'github.com', 'gitlab.com', 'bitbucket.org',
            'git.sr.ht', 'codeberg.org', 'gitea.com',
            'dev.azure.com', 'sourceforge.net'
        ]
        
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


def extract_repo_name(repo_url: str) -> str:
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


def get_repository_info(repo: Repo) -> dict:
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