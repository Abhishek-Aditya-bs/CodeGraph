# Code Graph - Folder Utilities
# Folder-related utility functions

import shutil
from pathlib import Path
from typing import Tuple
from git import Repo
from .file_utils import format_file_size, get_directory_size
from .git_utils import get_repository_info


def get_folder_statistics(folder_path: str) -> dict:
    """
    Get statistics about a local folder
    
    Args:
        folder_path: Path to the folder
        
    Returns:
        dict: Folder statistics
    """
    try:
        folder_path = Path(folder_path).resolve()
        
        if not folder_path.exists() or not folder_path.is_dir():
            return {'error': 'Folder does not exist or is not a directory'}
        
        stats = {
            'path': str(folder_path),
            'total_files': 0,
            'total_directories': 0,
            'total_size_bytes': 0,
            'file_extensions': {},
            'largest_files': [],
            'recent_files': []
        }
        
        files_with_size = []
        
        for item in folder_path.rglob('*'):
            if item.is_file():
                stats['total_files'] += 1
                try:
                    size = item.stat().st_size
                    stats['total_size_bytes'] += size
                    
                    # Track extensions
                    ext = item.suffix.lower()
                    if ext:
                        stats['file_extensions'][ext] = stats['file_extensions'].get(ext, 0) + 1
                    
                    # Collect file info for sorting
                    files_with_size.append({
                        'path': str(item.relative_to(folder_path)),
                        'size': size,
                        'modified': item.stat().st_mtime
                    })
                    
                except OSError:
                    continue
            elif item.is_dir():
                stats['total_directories'] += 1
        
        # Get largest files (top 5)
        files_with_size.sort(key=lambda x: x['size'], reverse=True)
        stats['largest_files'] = files_with_size[:5]
        
        # Get most recent files (top 5)
        files_with_size.sort(key=lambda x: x['modified'], reverse=True)
        stats['recent_files'] = files_with_size[:5]
        
        stats['total_size_human'] = format_file_size(stats['total_size_bytes'])
        
        return stats
        
    except Exception as e:
        return {'error': f'Error analyzing folder: {str(e)}'}


def list_cloned_repositories() -> list:
    """
    List all repositories that have been cloned to the project directory
    
    Returns:
        list: List of dictionaries with repository information
    """
    try:
        project_root = Path(__file__).parent.parent.parent
        cloned_repos_dir = project_root / "cloned_repos"
        
        if not cloned_repos_dir.exists():
            return []
        
        repositories = []
        for repo_dir in cloned_repos_dir.iterdir():
            if repo_dir.is_dir() and (repo_dir / ".git").exists():
                try:
                    repo = Repo(str(repo_dir))
                    repo_info = get_repository_info(repo)
                    repo_info['name'] = repo_dir.name
                    repo_info['path'] = str(repo_dir)
                    repo_info['size'] = get_directory_size(str(repo_dir))
                    repositories.append(repo_info)
                except Exception:
                    # If we can't read the repo, still list it
                    repositories.append({
                        'name': repo_dir.name,
                        'path': str(repo_dir),
                        'branch': 'unknown',
                        'latest_commit': 'unknown',
                        'author': 'unknown',
                        'size': get_directory_size(str(repo_dir))
                    })
        
        return repositories
        
    except Exception:
        return []


def cleanup_cloned_repositories(keep_recent: int = 5) -> Tuple[int, str]:
    """
    Clean up old cloned repositories, keeping only the most recent ones
    
    Args:
        keep_recent: Number of recent repositories to keep (default: 5)
        
    Returns:
        Tuple[int, str]: (number_removed, message)
    """
    try:
        project_root = Path(__file__).parent.parent.parent
        cloned_repos_dir = project_root / "cloned_repos"
        
        if not cloned_repos_dir.exists():
            return 0, "No cloned repositories directory found"
        
        # Get all repository directories sorted by modification time
        repo_dirs = [d for d in cloned_repos_dir.iterdir() if d.is_dir()]
        repo_dirs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        # Remove old repositories
        removed_count = 0
        if len(repo_dirs) > keep_recent:
            for repo_dir in repo_dirs[keep_recent:]:
                try:
                    shutil.rmtree(repo_dir)
                    removed_count += 1
                except Exception as e:
                    print(f"Warning: Could not remove {repo_dir}: {e}")
        
        message = f"Cleaned up {removed_count} old repositories, kept {min(len(repo_dirs), keep_recent)} recent ones"
        return removed_count, message
        
    except Exception as e:
        return 0, f"Error during cleanup: {str(e)}" 