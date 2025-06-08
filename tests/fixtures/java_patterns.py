# Code Graph - Java Design Patterns Test Fixtures
# Centralized test data management for Java Design Patterns repository

import os
import logging
from typing import List, Dict, Tuple, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class JavaPatternsTestData:
    """Manages test data from Java Design Patterns repository"""
    
    def __init__(self, repo_path: str, selected_patterns: List[str]):
        """
        Initialize test data manager
        
        Args:
            repo_path: Path to Java Design Patterns repository
            selected_patterns: List of pattern names to include in tests
        """
        self.repo_path = Path(repo_path)
        self.selected_patterns = selected_patterns
        self.pattern_paths = {}
        self._discover_patterns()
    
    def _discover_patterns(self) -> None:
        """Discover available pattern directories"""
        if not self.repo_path.exists():
            logger.warning(f"Repository path does not exist: {self.repo_path}")
            return
        
        for pattern in self.selected_patterns:
            # Try different possible directory structures
            possible_paths = [
                self.repo_path / pattern,
                self.repo_path / f"{pattern}-pattern",
                self.repo_path / pattern.replace("-", ""),
                self.repo_path / pattern.title(),
            ]
            
            for path in possible_paths:
                if path.exists() and path.is_dir():
                    self.pattern_paths[pattern] = path
                    logger.info(f"Found pattern '{pattern}' at: {path}")
                    break
            else:
                logger.warning(f"Pattern '{pattern}' not found in repository")
    
    def get_pattern_files(self, pattern: str, max_files: int = 10) -> List[Path]:
        """
        Get Java files for a specific pattern
        
        Args:
            pattern: Pattern name
            max_files: Maximum number of files to return
            
        Returns:
            List[Path]: Java files for the pattern
        """
        if pattern not in self.pattern_paths:
            logger.warning(f"Pattern '{pattern}' not available")
            return []
        
        pattern_path = self.pattern_paths[pattern]
        java_files = []
        
        # Recursively find Java files
        for java_file in pattern_path.rglob("*.java"):
            # Skip test files and build artifacts
            if any(skip in str(java_file).lower() for skip in ["test", "target", "build"]):
                continue
            java_files.append(java_file)
            
            if len(java_files) >= max_files:
                break
        
        logger.info(f"Found {len(java_files)} Java files for pattern '{pattern}'")
        return java_files
    
    def get_all_pattern_files(self, max_files_per_pattern: int = 10) -> Dict[str, List[Path]]:
        """
        Get Java files for all selected patterns
        
        Args:
            max_files_per_pattern: Maximum files per pattern
            
        Returns:
            Dict[str, List[Path]]: Pattern name to files mapping
        """
        all_files = {}
        
        for pattern in self.selected_patterns:
            files = self.get_pattern_files(pattern, max_files_per_pattern)
            if files:
                all_files[pattern] = files
        
        total_files = sum(len(files) for files in all_files.values())
        logger.info(f"Total files across all patterns: {total_files}")
        
        return all_files
    
    def get_expected_entities(self, pattern: str) -> Dict[str, List[str]]:
        """
        Get expected entities for a pattern (for validation)
        
        Args:
            pattern: Pattern name
            
        Returns:
            Dict[str, List[str]]: Expected entity types and names
        """
        # Define expected entities for each pattern
        expected_entities = {
            "singleton": {
                "classes": ["Singleton", "SingletonClass"],
                "methods": ["getInstance", "getSingletonInstance"],
                "concepts": ["thread-safe", "lazy initialization"]
            },
            "factory": {
                "classes": ["Factory", "ConcreteFactory", "Product", "ConcreteProduct"],
                "methods": ["createProduct", "makeProduct"],
                "concepts": ["object creation", "factory method"]
            },
            "observer": {
                "classes": ["Observer", "Subject", "ConcreteObserver", "ConcreteSubject"],
                "methods": ["notify", "update", "subscribe", "unsubscribe"],
                "concepts": ["event handling", "publish-subscribe"]
            },
            "strategy": {
                "classes": ["Strategy", "ConcreteStrategy", "Context"],
                "methods": ["execute", "doAlgorithm"],
                "concepts": ["algorithm selection", "runtime behavior"]
            },
            "decorator": {
                "classes": ["Decorator", "ConcreteDecorator", "Component"],
                "methods": ["decorate", "wrap"],
                "concepts": ["object wrapping", "behavior extension"]
            },
            "command": {
                "classes": ["Command", "ConcreteCommand", "Invoker", "Receiver"],
                "methods": ["execute", "undo", "invoke"],
                "concepts": ["encapsulate request", "undo operations"]
            },
            "adapter": {
                "classes": ["Adapter", "Adaptee", "Target"],
                "methods": ["adapt", "convert"],
                "concepts": ["interface conversion", "legacy integration"]
            }
        }
        
        return expected_entities.get(pattern, {})
    
    def get_test_queries(self, pattern: Optional[str] = None) -> List[str]:
        """
        Get test queries for patterns
        
        Args:
            pattern: Specific pattern name, or None for general queries
            
        Returns:
            List[str]: Test queries
        """
        if pattern:
            pattern_queries = {
                "singleton": [
                    "Show me the Singleton pattern implementation",
                    "How is thread safety handled in Singleton?",
                    "Find the getInstance method"
                ],
                "factory": [
                    "How does the Factory pattern work?",
                    "Show me factory method implementations",
                    "What products are created by the factory?"
                ],
                "observer": [
                    "What classes implement the Observer interface?",
                    "How does the notification mechanism work?",
                    "Show me observer pattern relationships"
                ],
                "strategy": [
                    "Find method calls in the Strategy pattern",
                    "How are different algorithms selected?",
                    "Show me strategy implementations"
                ]
            }
            return pattern_queries.get(pattern, [])
        
        # General queries across all patterns
        return [
            "Show me design pattern implementations",
            "Find all interface implementations",
            "What are the main classes in each pattern?",
            "How do these patterns handle object creation?",
            "Show me method relationships between classes"
        ]
    
    def validate_repository(self) -> Tuple[bool, str]:
        """
        Validate that the repository is properly set up
        
        Returns:
            Tuple[bool, str]: (is_valid, message)
        """
        if not self.repo_path.exists():
            return False, f"Repository path does not exist: {self.repo_path}"
        
        if not self.pattern_paths:
            return False, "No patterns found in repository"
        
        total_files = 0
        for pattern, path in self.pattern_paths.items():
            files = self.get_pattern_files(pattern, max_files=100)
            total_files += len(files)
        
        if total_files == 0:
            return False, "No Java files found in any pattern"
        
        return True, f"Repository valid: {len(self.pattern_paths)} patterns, {total_files} Java files"


def get_test_data_manager(repo_path: str, selected_patterns: List[str]) -> JavaPatternsTestData:
    """
    Factory function to create test data manager
    
    Args:
        repo_path: Path to Java Design Patterns repository
        selected_patterns: List of pattern names
        
    Returns:
        JavaPatternsTestData: Test data manager instance
    """
    return JavaPatternsTestData(repo_path, selected_patterns) 