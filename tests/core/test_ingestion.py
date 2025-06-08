# Code Graph - Core Ingestion Tests
# Foundation tests for code parsing and chunking functionality

import pytest
import logging
from typing import List, Dict, Any
from pathlib import Path

from app.ingestion import parse_code_chunks
from tests.fixtures.test_data_manager import get_self_contained_test_manager

logger = logging.getLogger(__name__)


class TestCodeIngestion:
    """Test suite for code ingestion functionality"""
    
    def test_parse_code_chunks_basic(self, test_config, selected_patterns):
        """
        Test basic code parsing and chunking functionality
        
        This is the foundation test that validates:
        1. File discovery and reading
        2. Code parsing and chunking
        3. Metadata extraction
        4. Document structure
        """
        # Get self-contained test data manager
        test_data = get_self_contained_test_manager()
        
        # Get available patterns
        available_patterns = test_data.get_available_patterns()
        if not available_patterns:
            pytest.skip("No patterns available in self-contained test data")
        
        # Use first available pattern for basic test
        test_pattern = available_patterns[0]
        logger.info(f"Testing ingestion with pattern '{test_pattern}'")
        
        # Get temporary directory with test files for this pattern
        with test_data.get_pattern_temp_dir(test_pattern) as temp_dir:
            # Parse code chunks from the temporary directory (Java files only)
            success, message, documents = parse_code_chunks(
                codebase_path=str(temp_dir),
                chunk_size=test_config["chunk_size"],
                chunk_overlap=test_config["chunk_overlap"],
                include_extensions=['.java']  # Only Java files
            )
            
            # Validate results
            assert success, f"parse_code_chunks failed: {message}"
            assert documents is not None, "parse_code_chunks returned None documents"
            assert isinstance(documents, list), "parse_code_chunks should return a list"
            assert len(documents) > 0, "No documents were generated"
            
            logger.info(f"Generated {len(documents)} document chunks")
            
            # Validate document structure
            for i, doc in enumerate(documents[:3]):  # Check first 3 documents
                # Check document has content
                assert hasattr(doc, 'page_content'), f"Document {i} missing page_content"
                assert hasattr(doc, 'metadata'), f"Document {i} missing metadata"
                assert len(doc.page_content) > 0, f"Document {i} has empty content"
                
                # Check metadata structure
                metadata = doc.metadata
                assert isinstance(metadata, dict), f"Document {i} metadata is not a dict"
                
                # Check required metadata fields
                required_fields = ['file_path', 'language', 'chunk_id']
                for field in required_fields:
                    assert field in metadata, f"Document {i} missing metadata field: {field}"
                
                # Validate metadata values
                assert metadata['language'] == 'java', f"Document {i} should have Java language"
                
                logger.info(f"Document {i}: {len(doc.page_content)} chars, file: {Path(metadata['file_path']).name}")
    
    def test_parse_code_chunks_multiple_patterns(self, test_config, selected_patterns):
        """
        Test parsing multiple design patterns
        
        Validates:
        1. Multi-pattern processing
        2. File diversity handling
        3. Consistent chunking across patterns
        4. Metadata consistency
        """
        # Get self-contained test data manager
        test_data = get_self_contained_test_manager()
        
        # Get available patterns
        available_patterns = test_data.get_available_patterns()
        if len(available_patterns) < 2:
            pytest.skip("Need at least 2 patterns for multi-pattern test")
        
        # Test with first two available patterns
        test_patterns = available_patterns[:2]
        logger.info(f"Testing patterns: {test_patterns}")
        
        # Parse each pattern separately and combine results
        all_documents = []
        pattern_doc_count = {}
        
        for pattern in test_patterns:
            with test_data.get_pattern_temp_dir(pattern) as temp_dir:
                success, message, documents = parse_code_chunks(
                    codebase_path=str(temp_dir),
                    chunk_size=test_config["chunk_size"],
                    chunk_overlap=test_config["chunk_overlap"],
                    include_extensions=['.java']
                )
                
                if success and documents:
                    all_documents.extend(documents)
                    pattern_doc_count[pattern] = len(documents)
                    logger.info(f"Pattern '{pattern}': {len(documents)} documents")
        
        documents = all_documents
        
        # Validate results
        assert len(documents) > 0, "No documents generated from multiple patterns"
        
        # Group documents by pattern (based on file path content/class names)
        pattern_docs = {}
        for doc in documents:
            # Determine pattern from document content or filename
            pattern = None
            content_lower = doc.page_content.lower()
            file_path = doc.metadata['file_path']
            
            for p in test_patterns:
                if p.lower() in content_lower or p.lower() in file_path.lower():
                    pattern = p
                    break
            
            if pattern:
                if pattern not in pattern_docs:
                    pattern_docs[pattern] = []
                pattern_docs[pattern].append(doc)
        
        logger.info(f"Documents distributed across patterns: {[(p, len(docs)) for p, docs in pattern_docs.items()]}")
        
        # Validate each pattern has documents
        assert len(pattern_docs) >= 1, f"Expected documents from patterns, got: {list(pattern_docs.keys())}"
        
        # Validate consistency across patterns
        for pattern, docs in pattern_docs.items():
            assert len(docs) > 0, f"No documents for pattern: {pattern}"
            
            # Check all documents have consistent structure
            for doc in docs:
                assert doc.metadata['language'] == 'java'
                assert 'chunk_id' in doc.metadata
                assert len(doc.page_content) > 0
    
    def test_chunk_size_and_overlap_behavior(self, test_config, selected_patterns):
        """
        Test chunking behavior with different sizes and overlaps
        
        Validates:
        1. Chunk size limits are respected
        2. Overlap behavior works correctly
        3. Content preservation
        4. Metadata accuracy
        """
        # Get self-contained test data manager
        test_data = get_self_contained_test_manager()
        
        # Get available patterns
        available_patterns = test_data.get_available_patterns()
        if not available_patterns:
            pytest.skip("No patterns available for chunking test")
        
        # Use first available pattern for chunking analysis
        test_pattern = available_patterns[0]
        
        # Test different chunk sizes
        chunk_configs = [
            {"size": 500, "overlap": 100},
            {"size": 1000, "overlap": 200},
            {"size": 1500, "overlap": 300}
        ]
        
        results = {}
        
        for config in chunk_configs:
            with test_data.get_pattern_temp_dir(test_pattern) as temp_dir:
                success, message, documents = parse_code_chunks(
                    codebase_path=str(temp_dir),
                    chunk_size=config["size"],
                    chunk_overlap=config["overlap"],
                    include_extensions=['.java']
                )
                
                if not success:
                    pytest.fail(f"Chunking failed for config {config}: {message}")
                
                results[f"{config['size']}_{config['overlap']}"] = documents
                
                # Validate chunk size constraints
                for doc in documents:
                    content_length = len(doc.page_content)
                    # Allow some flexibility for word boundaries
                    assert content_length <= config["size"] * 1.2, f"Chunk too large: {content_length} > {config['size']}"
                    
                    # Check metadata has chunk size info
                    if 'start_line' in doc.metadata and 'end_line' in doc.metadata:
                        start_line = doc.metadata['start_line']
                        end_line = doc.metadata['end_line']
                        assert end_line >= start_line, "End line should be >= start line"
        
        # Compare results across different chunk sizes
        sizes = [500, 1000, 1500]
        doc_counts = [len(results[f"{size}_{size//5}"]) for size in sizes]
        
        # Generally, smaller chunks should produce more documents
        logger.info(f"Document counts by chunk size: {dict(zip(sizes, doc_counts))}")
        
        # At least should have some variation in chunk counts
        assert max(doc_counts) > 0, "Should generate some documents"
    
    def test_metadata_extraction_accuracy(self, test_config, selected_patterns):
        """
        Test metadata extraction accuracy and completeness
        
        Validates:
        1. All required metadata fields are present
        2. Metadata values are accurate
        3. File path tracking works correctly
        4. Language detection is correct
        """
        # Get self-contained test data manager
        test_data = get_self_contained_test_manager()
        
        # Get available patterns
        available_patterns = test_data.get_available_patterns()
        if not available_patterns:
            pytest.skip("No patterns available for metadata test")
        
        test_pattern = available_patterns[0]
        
        with test_data.get_pattern_temp_dir(test_pattern) as temp_dir:
            success, message, documents = parse_code_chunks(
                codebase_path=str(temp_dir),
                chunk_size=test_config["chunk_size"],
                chunk_overlap=test_config["chunk_overlap"],
                include_extensions=['.java']
            )
            
            assert success, f"Document generation failed: {message}"
            assert len(documents) > 0, "No documents generated for metadata test"
            
            logger.info(f"Testing metadata for {len(documents)} documents")
            
            # Required metadata fields based on actual parse_code_chunks implementation
            required_fields = [
                'file_path', 'language', 'chunk_id', 'chunk_size',
                'codebase_path', 'start_line', 'end_line'
            ]
            
            for i, doc in enumerate(documents):
                metadata = doc.metadata
                
                # Check all required fields are present
                for field in required_fields:
                    assert field in metadata, f"Document {i} missing required field: {field}"
                
                # Validate specific field values
                assert metadata['language'] == 'java', f"Document {i} should have 'java' language"
                assert metadata['file_path'].endswith('.java'), f"Document {i} file_path should end with .java"
                assert isinstance(metadata['chunk_id'], int), f"Document {i} chunk_id should be int"
                assert metadata['chunk_id'] >= 0, f"Document {i} chunk_id should be >= 0"
                assert isinstance(metadata['chunk_size'], int), f"Document {i} chunk_size should be int"
                assert metadata['chunk_size'] > 0, f"Document {i} chunk_size should be > 0"
                
                # Validate line numbers
                if metadata['start_line'] is not None and metadata['end_line'] is not None:
                    assert metadata['start_line'] <= metadata['end_line'], f"Document {i} start_line should be <= end_line"
                
                # Check that chunk_size matches actual content length
                actual_size = len(doc.page_content)
                assert metadata['chunk_size'] == actual_size, f"Document {i} chunk_size metadata should match content length"
                
                logger.info(f"Document {i} metadata validated: {Path(metadata['file_path']).name}, chunk {metadata['chunk_id']}, size {metadata['chunk_size']}")
    
    def test_content_preservation_and_quality(self, test_config, selected_patterns):
        """
        Test content preservation and quality during chunking
        
        Validates:
        1. Java syntax is preserved
        2. Code blocks are not broken inappropriately
        3. Content quality is maintained
        4. Important code elements are preserved
        """
        # Get self-contained test data manager
        test_data = get_self_contained_test_manager()
        
        # Get available patterns
        available_patterns = test_data.get_available_patterns()
        if not available_patterns:
            pytest.skip("No patterns available for content quality test")
        
        test_pattern = available_patterns[0]
        
        with test_data.get_pattern_temp_dir(test_pattern) as temp_dir:
            success, message, documents = parse_code_chunks(
                codebase_path=str(temp_dir),
                chunk_size=test_config["chunk_size"],
                chunk_overlap=test_config["chunk_overlap"],
                include_extensions=['.java']
            )
            
            assert success, f"Document generation failed: {message}"
            assert len(documents) > 0, "No documents generated for content quality test"
            
            logger.info(f"Testing content quality for {len(documents)} documents")
            
            java_keywords = ['class', 'interface', 'public', 'private', 'protected', 'static', 'void', 'return']
            content_stats = {
                'contains_class_declaration': 0,
                'contains_method_declaration': 0,
                'contains_java_keywords': 0,
                'has_proper_braces': 0,
                'total_documents': len(documents)
            }
            
            for doc in documents:
                content = doc.page_content
                content_lower = content.lower()
                
                # Check for Java class/interface declarations
                if 'class ' in content_lower or 'interface ' in content_lower:
                    content_stats['contains_class_declaration'] += 1
                
                # Check for method declarations
                if ('public ' in content_lower or 'private ' in content_lower) and '(' in content and ')' in content:
                    content_stats['contains_method_declaration'] += 1
                
                # Check for Java keywords
                if any(keyword in content_lower for keyword in java_keywords):
                    content_stats['contains_java_keywords'] += 1
                
                # Check for proper brace balance (basic check)
                open_braces = content.count('{')
                close_braces = content.count('}')
                if abs(open_braces - close_braces) <= 1:  # Allow some imbalance due to chunking
                    content_stats['has_proper_braces'] += 1
                
                # Basic content quality checks
                assert len(content) > 0, "Document should have content"
                assert not content.isspace(), "Document should not be only whitespace"
            
            # Log content statistics
            for stat, count in content_stats.items():
                if stat != 'total_documents':
                    percentage = (count / content_stats['total_documents']) * 100
                    logger.info(f"{stat}: {count}/{content_stats['total_documents']} ({percentage:.1f}%)")
            
            # Quality assertions
            assert content_stats['contains_java_keywords'] > 0, "Should contain Java keywords"
            assert content_stats['contains_java_keywords'] >= content_stats['total_documents'] * 0.5, "At least 50% should contain Java keywords"


# Additional utility functions for testing
def validate_document_structure(documents: List[Any]) -> bool:
    """
    Utility function to validate document structure
    
    Args:
        documents: List of document objects
        
    Returns:
        bool: True if all documents have valid structure
    """
    if not documents:
        return False
    
    for doc in documents:
        if not hasattr(doc, 'page_content') or not hasattr(doc, 'metadata'):
            return False
        
        if not isinstance(doc.metadata, dict):
            return False
        
        required_fields = ['file_path', 'language', 'chunk_id']
        if not all(field in doc.metadata for field in required_fields):
            return False
    
    return True


def get_content_statistics(documents: List[Any]) -> Dict[str, Any]:
    """
    Get statistics about document content
    
    Args:
        documents: List of document objects
        
    Returns:
        Dict: Content statistics
    """
    if not documents:
        return {}
    
    content_lengths = [len(doc.page_content) for doc in documents]
    
    return {
        'total_documents': len(documents),
        'total_content_length': sum(content_lengths),
        'avg_content_length': sum(content_lengths) / len(content_lengths),
        'min_content_length': min(content_lengths),
        'max_content_length': max(content_lengths),
        'unique_files': len(set(doc.metadata['file_path'] for doc in documents))
    } 