"""
Self-contained test data manager for CodeGraph testing.
Replaces dependency on external repositories with built-in sample code.
"""

import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any
from contextlib import contextmanager
from langchain.schema import Document

from .sample_java_code import get_sample_code_files, get_pattern_examples


class SelfContainedTestDataManager:
    """
    Manages test data using self-contained sample code instead of external repositories.
    Creates temporary file structure for testing GraphRAG functionality.
    """
    
    def __init__(self):
        self.temp_dir = None
        self.sample_files = get_sample_code_files()
        self.pattern_examples = get_pattern_examples()
    
    def setup_temp_codebase(self) -> Path:
        """
        Create a temporary codebase with sample Java files.
        Returns the path to the temporary directory.
        """
        self.temp_dir = Path(tempfile.mkdtemp(prefix="codegraph_test_"))
        
        # Create directory structure and files
        for file_path, content in self.sample_files.items():
            full_path = self.temp_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)
        
        return self.temp_dir
    
    @contextmanager
    def get_pattern_temp_dir(self, pattern: str):
        """
        Context manager that creates a temporary directory with files for a specific pattern.
        Yields the path to the temporary directory and cleans up automatically.
        """
        pattern_temp_dir = Path(tempfile.mkdtemp(prefix=f"codegraph_test_{pattern}_"))
        
        try:
            # Create files for the specified pattern
            pattern_files = {
                file_path: content 
                for file_path, content in self.sample_files.items()
                if pattern.lower() in file_path.lower()
            }
            
            if not pattern_files:
                # If no pattern-specific files, create at least one sample file
                pattern_files = {
                    f"{pattern}/Sample{pattern.capitalize()}.java": self._get_sample_pattern_content(pattern)
                }
            
            # Create directory structure and files
            for file_path, content in pattern_files.items():
                full_path = pattern_temp_dir / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(content)
            
            yield pattern_temp_dir
            
        finally:
            # Clean up the temporary directory
            if pattern_temp_dir.exists():
                shutil.rmtree(pattern_temp_dir)
    
    def _get_sample_pattern_content(self, pattern: str) -> str:
        """Generate sample content for a pattern if no specific files exist"""
        if pattern.lower() == "adapter":
            return '''package com.example.adapter;

public class SampleAdapter {
    private final SampleAdaptee adaptee;
    
    public SampleAdapter(SampleAdaptee adaptee) {
        this.adaptee = adaptee;
    }
    
    public void request() {
        adaptee.specificRequest();
    }
}

class SampleAdaptee {
    public void specificRequest() {
        System.out.println("Specific request handled");
    }
}'''
        elif pattern.lower() == "factory":
            return '''package com.example.factory;

public abstract class SampleFactory {
    public abstract SampleProduct createProduct();
}

class ConcreteSampleFactory extends SampleFactory {
    @Override
    public SampleProduct createProduct() {
        return new ConcreteSampleProduct();
    }
}

interface SampleProduct {
    void use();
}

class ConcreteSampleProduct implements SampleProduct {
    @Override
    public void use() {
        System.out.println("Using concrete product");
    }
}'''
        elif pattern.lower() == "observer":
            return '''package com.example.observer;

import java.util.ArrayList;
import java.util.List;

public class SampleSubject {
    private List<SampleObserver> observers = new ArrayList<>();
    private String state;
    
    public void attach(SampleObserver observer) {
        observers.add(observer);
    }
    
    public void notifyObservers() {
        for (SampleObserver observer : observers) {
            observer.update(state);
        }
    }
    
    public void setState(String state) {
        this.state = state;
        notifyObservers();
    }
}

interface SampleObserver {
    void update(String state);
}

class ConcreteSampleObserver implements SampleObserver {
    @Override
    public void update(String state) {
        System.out.println("Observer updated with state: " + state);
    }
}'''
        else:
            return f'''package com.example.{pattern.lower()};

public class Sample{pattern.capitalize()} {{
    public void execute() {{
        System.out.println("Executing {pattern} pattern");
    }}
}}'''
    
    def cleanup(self):
        """Clean up temporary directory"""
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            self.temp_dir = None
    
    def get_sample_documents(self, max_docs: int = 10) -> List[Document]:
        """
        Get sample documents for testing without needing external repositories.
        """
        documents = []
        
        for i, (file_path, content) in enumerate(self.sample_files.items()):
            if len(documents) >= max_docs:
                break
                
            # Determine language from file extension
            language = "java" if file_path.endswith(".java") else "unknown"
            
            # Create document with proper metadata
            doc = Document(
                page_content=content.strip(),
                metadata={
                    "file_path": file_path,
                    "language": language,
                    "start_line": 1,
                    "end_line": len(content.split('\n')),
                    "chunk_id": f"test_chunk_{i}",
                    "pattern": self._detect_pattern(file_path)
                }
            )
            documents.append(doc)
        
        return documents
    
    def get_pattern_documents(self, pattern: str, max_docs: int = 5) -> List[Document]:
        """Get documents for a specific design pattern"""
        pattern_docs = []
        
        for file_path, content in self.sample_files.items():
            if pattern.lower() in file_path.lower():
                if len(pattern_docs) >= max_docs:
                    break
                    
                doc = Document(
                    page_content=content.strip(),
                    metadata={
                        "file_path": file_path,
                        "language": "java",
                        "start_line": 1,
                        "end_line": len(content.split('\n')),
                        "chunk_id": f"{pattern}_chunk_{len(pattern_docs)}",
                        "pattern": pattern
                    }
                )
                pattern_docs.append(doc)
        
        return pattern_docs
    
    def _detect_pattern(self, file_path: str) -> str:
        """Detect design pattern from file path"""
        if "adapter" in file_path.lower():
            return "adapter"
        elif "factory" in file_path.lower():
            return "factory"
        elif "observer" in file_path.lower():
            return "observer"
        else:
            return "general"
    
    def get_available_patterns(self) -> List[str]:
        """Get list of available design patterns"""
        return ["adapter", "factory", "observer"]


def get_self_contained_test_manager() -> SelfContainedTestDataManager:
    """Factory function to get test data manager"""
    return SelfContainedTestDataManager()


# Legacy compatibility function
def get_test_data_manager(java_patterns_path: str = None, selected_patterns: List[str] = None):
    """
    Legacy compatibility function that now uses self-contained data.
    This replaces the old external repository dependency.
    """
    manager = SelfContainedTestDataManager()
    
    # Create a mock object that behaves like the old manager
    class CompatibilityWrapper:
        def __init__(self, manager: SelfContainedTestDataManager):
            self.manager = manager
            self.pattern_paths = {
                pattern: f"mock_path/{pattern}" 
                for pattern in manager.get_available_patterns()
            }
        
        def get_documents(self, max_docs: int = 10) -> List[Document]:
            return self.manager.get_sample_documents(max_docs)
        
        def cleanup(self):
            self.manager.cleanup()
    
    return CompatibilityWrapper(manager) 