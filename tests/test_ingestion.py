# Code Graph - Ingestion Tests
# Test functions for the ingestion module

import shutil
from pathlib import Path
from app.ingestion import clone_repository, read_local_folder, parse_code_chunks, discover_code_files


def test_repository_cloning(test_repo_url: str = "https://github.com/octocat/Hello-World.git", cleanup_after: bool = True) -> bool:
    """
    Test the repository cloning functionality with a public repository
    
    Args:
        test_repo_url: URL of a public repository to test with
        cleanup_after: Whether to clean up the test repository after testing
        
    Returns:
        bool: True if test passed, False otherwise
    """
    print(f"🧪 Testing repository cloning with: {test_repo_url}")
    
    # Test with temporary directory to avoid cluttering project
    success, message, cloned_path = clone_repository(test_repo_url, use_project_dir=False)
    
    print(f"📊 Test Result: {'PASSED' if success else 'FAILED'}")
    print(f"📝 Message: {message}")
    
    if success and cloned_path:
        # Verify some basic files exist
        files_found = list(Path(cloned_path).rglob("*"))[:5]  # First 5 files
        print(f"📁 Files found: {len(files_found)} (showing first 5)")
        for file_path in files_found:
            if file_path.is_file():
                print(f"   - {file_path.name}")
        
        # Clean up test directory if requested
        if cleanup_after:
            try:
                shutil.rmtree(cloned_path)
                print("🧹 Test directory cleaned up")
            except Exception as e:
                print(f"⚠️ Warning: Could not clean up test directory: {e}")
    
    return success


def test_local_folder_reading(test_folder_path: str) -> bool:
    """
    Test the local folder validation functionality
    
    Args:
        test_folder_path: Path to a test folder
        
    Returns:
        bool: True if test passed, False otherwise
    """
    print(f"🧪 Testing local folder validation with: {test_folder_path}")
    
    # Test folder validation
    success, message, validated_path = read_local_folder(test_folder_path)
    
    print(f"📊 Validation Result: {'PASSED' if success else 'FAILED'}")
    print(f"📝 Message: {message}")
    
    if success and validated_path:
        print(f"✅ Validated path: {validated_path}")
        
        # Test file discovery
        print(f"\n🔍 Testing file discovery...")
        disc_success, disc_message, file_data = discover_code_files(validated_path)
        
        if disc_success and file_data:
            print(f"📁 Sample files discovered:")
            for file_info in file_data[:5]:  # Show first 5 files
                print(f"   - {file_info['relative_path']} ({file_info['size_human']}, {file_info['lines']} lines)")
            
            if len(file_data) > 5:
                print(f"   ... and {len(file_data) - 5} more files")
    
    return success


def test_code_chunking(test_path: str, chunk_size: int = 300) -> bool:
    """
    Test the code chunking functionality
    
    Args:
        test_path: Path to test (can be from clone_repository or read_local_folder)
        chunk_size: Size of chunks for testing
        
    Returns:
        bool: True if test passed, False otherwise
    """
    print(f"🧪 Testing code chunking with: {test_path}")
    
    # Test chunking
    success, message, chunks = parse_code_chunks(test_path, chunk_size=chunk_size, include_extensions=['.py', '.java', '.md'])
    
    print(f"📊 Chunking Result: {'PASSED' if success else 'FAILED'}")
    print(f"📝 Message: {message}")
    
    if success and chunks:
        print(f"\n📄 Sample chunks:")
        for i, chunk in enumerate(chunks[:3]):  # Show first 3 chunks
            print(f"   Chunk {i+1}:")
            print(f"     📁 File: {chunk.metadata.get('filename', 'Unknown')}")
            print(f"     📏 Size: {chunk.metadata.get('chunk_size', 0)} chars")
            print(f"     📝 Preview: {chunk.page_content[:100]}...")
            print()
        
        if len(chunks) > 3:
            print(f"   ... and {len(chunks) - 3} more chunks")
    
    return success


def run_all_tests():
    """
    Run all ingestion tests
    """
    print("🧪 RUNNING ALL INGESTION TESTS")
    print("=" * 50)
    
    # Test 1: Repository cloning
    print("\n1️⃣ Testing Repository Cloning:")
    test1_result = test_repository_cloning()
    
    # Test 2: Local folder reading
    print("\n2️⃣ Testing Local Folder Reading:")
    test2_result = test_local_folder_reading("./app")
    
    # Test 3: Code chunking
    print("\n3️⃣ Testing Code Chunking:")
    test3_result = test_code_chunking("./app")
    
    # Summary
    print("\n📊 TEST SUMMARY:")
    print("=" * 50)
    print(f"Repository Cloning: {'✅ PASSED' if test1_result else '❌ FAILED'}")
    print(f"Local Folder Reading: {'✅ PASSED' if test2_result else '❌ FAILED'}")
    print(f"Code Chunking: {'✅ PASSED' if test3_result else '❌ FAILED'}")
    
    all_passed = test1_result and test2_result and test3_result
    print(f"\nOverall Result: {'🎉 ALL TESTS PASSED' if all_passed else '⚠️ SOME TESTS FAILED'}")
    
    return all_passed


if __name__ == "__main__":
    run_all_tests() 