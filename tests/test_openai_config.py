# Code Graph - OpenAI Configuration Tests
# Test functions for OpenAI API key setup and functionality

import os
import json
import subprocess
from app.config import Config


def test_openai_api_key_config() -> bool:
    """
    Test if OpenAI API key is properly configured in Config
    
    Returns:
        bool: True if test passed, False otherwise
    """
    print("🧪 Testing OpenAI API key configuration...")
    
    try:
        # Test Config loading
        config = Config()
        
        # Check if OPENAI_API_KEY is loaded
        if not hasattr(config, 'OPENAI_API_KEY'):
            print("❌ Config class doesn't have OPENAI_API_KEY attribute")
            return False
        
        api_key = config.OPENAI_API_KEY
        
        if not api_key:
            print("❌ OPENAI_API_KEY is empty or None")
            print("💡 Make sure you have set OPENAI_API_KEY in your .env file")
            return False
        
        if api_key.startswith('your_') or api_key == 'your_openai_api_key_here':
            print("❌ OPENAI_API_KEY appears to be a placeholder")
            print("💡 Please set a real OpenAI API key in your .env file")
            return False
        
        # Check if it looks like a valid OpenAI API key format
        if not api_key.startswith('sk-'):
            print("❌ OPENAI_API_KEY doesn't start with 'sk-' (expected format)")
            print(f"🔍 Current value starts with: {api_key[:10]}...")
            return False
        
        print("✅ OpenAI API key is properly configured")
        print(f"🔑 API key format: {api_key[:7]}...{api_key[-4:]} (length: {len(api_key)})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing OpenAI API key config: {str(e)}")
        return False


def test_openai_api_key_environment() -> bool:
    """
    Test if OpenAI API key is accessible from environment variables
    
    Returns:
        bool: True if test passed, False otherwise
    """
    print("🧪 Testing OpenAI API key environment access...")
    
    try:
        # Check direct environment variable access
        env_api_key = os.getenv('OPENAI_API_KEY')
        
        if not env_api_key:
            print("❌ OPENAI_API_KEY not found in environment variables")
            print("💡 Make sure your .env file is in the project root and contains OPENAI_API_KEY=your_key")
            return False
        
        print("✅ OpenAI API key found in environment")
        print(f"🔑 Environment key format: {env_api_key[:7]}...{env_api_key[-4:]} (length: {len(env_api_key)})")
        
        # Compare with Config
        config = Config()
        if hasattr(config, 'OPENAI_API_KEY') and config.OPENAI_API_KEY == env_api_key:
            print("✅ Config and environment API keys match")
        else:
            print("⚠️ Config and environment API keys don't match")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing environment API key: {str(e)}")
        return False


def test_openai_api_curl() -> bool:
    """
    Test OpenAI API using curl command to verify the key works
    
    Returns:
        bool: True if test passed, False otherwise
    """
    print("🧪 Testing OpenAI API with curl command...")
    
    try:
        config = Config()
        
        if not hasattr(config, 'OPENAI_API_KEY') or not config.OPENAI_API_KEY:
            print("❌ No OpenAI API key available for testing")
            return False
        
        api_key = config.OPENAI_API_KEY
        
        # Prepare curl command for OpenAI API
        curl_command = [
            'curl',
            '-s',  # Silent mode
            '-X', 'POST',
            'https://api.openai.com/v1/chat/completions',
            '-H', 'Content-Type: application/json',
            '-H', f'Authorization: Bearer {api_key}',
            '-d', json.dumps({
                "model": "gpt-4o-mini",
                "messages": [
                    {
                        "role": "user",
                        "content": "Say 'Hello from Code Graph!' in exactly 5 words."
                    }
                ],
                "max_tokens": 10,
                "temperature": 0
            })
        ]
        
        print("🔄 Making API call to OpenAI...")
        print(f"📡 Model: gpt-4o-mini")
        print(f"💬 Test message: 'Say Hello from Code Graph! in exactly 5 words.'")
        
        # Execute curl command
        result = subprocess.run(curl_command, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            print(f"❌ Curl command failed with return code: {result.returncode}")
            print(f"🔍 Error: {result.stderr}")
            return False
        
        # Parse response
        try:
            response_data = json.loads(result.stdout)
            
            if 'error' in response_data:
                error_info = response_data['error']
                print(f"❌ OpenAI API Error: {error_info.get('message', 'Unknown error')}")
                print(f"🔍 Error type: {error_info.get('type', 'Unknown')}")
                print(f"🔍 Error code: {error_info.get('code', 'Unknown')}")
                return False
            
            if 'choices' in response_data and len(response_data['choices']) > 0:
                message_content = response_data['choices'][0]['message']['content']
                usage = response_data.get('usage', {})
                
                print("✅ OpenAI API call successful!")
                print(f"🤖 Response: {message_content}")
                print(f"📊 Tokens used: {usage.get('total_tokens', 'Unknown')}")
                print(f"💰 Prompt tokens: {usage.get('prompt_tokens', 'Unknown')}")
                print(f"💰 Completion tokens: {usage.get('completion_tokens', 'Unknown')}")
                
                return True
            else:
                print("❌ Unexpected response format from OpenAI API")
                print(f"🔍 Response: {result.stdout}")
                return False
                
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse OpenAI API response as JSON: {str(e)}")
            print(f"🔍 Raw response: {result.stdout}")
            return False
        
    except subprocess.TimeoutExpired:
        print("❌ OpenAI API call timed out (30 seconds)")
        return False
    except Exception as e:
        print(f"❌ Error testing OpenAI API with curl: {str(e)}")
        return False


def test_langchain_openai_integration() -> bool:
    """
    Test OpenAI integration using LangChain (same as our knowledge graph implementation)
    
    Returns:
        bool: True if test passed, False otherwise
    """
    print("🧪 Testing LangChain OpenAI integration...")
    
    try:
        from langchain_openai import ChatOpenAI
        from app.config import Config
        
        config = Config()
        
        if not hasattr(config, 'OPENAI_API_KEY') or not config.OPENAI_API_KEY:
            print("❌ No OpenAI API key available for LangChain testing")
            return False
        
        # Initialize ChatOpenAI with same configuration as knowledge graph
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            openai_api_key=config.OPENAI_API_KEY
        )
        
        print("🔄 Testing LangChain ChatOpenAI with gpt-4o-mini...")
        
        # Test with a simple message
        test_message = "Respond with exactly: 'LangChain test successful'"
        response = llm.invoke(test_message)
        
        print("✅ LangChain OpenAI integration successful!")
        print(f"🤖 Response: {response.content}")
        print(f"📊 Response type: {type(response)}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Missing LangChain dependency: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Error testing LangChain OpenAI integration: {str(e)}")
        return False


def run_all_openai_tests():
    """
    Run all OpenAI configuration and functionality tests
    """
    print("🧪 RUNNING ALL OPENAI CONFIGURATION TESTS")
    print("=" * 60)
    
    # Test 1: Config access
    print("\n1️⃣ Testing OpenAI API Key Configuration:")
    test1_result = test_openai_api_key_config()
    
    # Test 2: Environment access
    print("\n2️⃣ Testing Environment Variable Access:")
    test2_result = test_openai_api_key_environment()
    
    # Test 3: Curl API test
    print("\n3️⃣ Testing OpenAI API with Curl:")
    test3_result = test_openai_api_curl()
    
    # Test 4: LangChain integration
    print("\n4️⃣ Testing LangChain OpenAI Integration:")
    test4_result = test_langchain_openai_integration()
    
    # Summary
    print("\n📊 OPENAI TEST SUMMARY:")
    print("=" * 60)
    print(f"API Key Configuration: {'✅ PASSED' if test1_result else '❌ FAILED'}")
    print(f"Environment Variable Access: {'✅ PASSED' if test2_result else '❌ FAILED'}")
    print(f"OpenAI API Curl Test: {'✅ PASSED' if test3_result else '❌ FAILED'}")
    print(f"LangChain Integration: {'✅ PASSED' if test4_result else '❌ FAILED'}")
    
    all_passed = all([test1_result, test2_result, test3_result, test4_result])
    print(f"\nOverall Result: {'🎉 ALL TESTS PASSED' if all_passed else '⚠️ SOME TESTS FAILED'}")
    
    if all_passed:
        print("\n💡 OpenAI Setup Complete!")
        print("   ✅ API key properly configured")
        print("   ✅ Environment variables working")
        print("   ✅ API connectivity verified")
        print("   ✅ LangChain integration ready")
        print("\n🚀 Ready to run full knowledge graph generation tests!")
        print("   Run: python -m tests.test_knowledge_graph")
    else:
        print("\n🔧 Troubleshooting Tips:")
        if not test1_result or not test2_result:
            print("   1. Check that .env file exists in project root")
            print("   2. Verify OPENAI_API_KEY=sk-... is in .env file")
            print("   3. Restart your terminal/IDE to reload environment")
        if not test3_result:
            print("   4. Verify your OpenAI API key is valid and has credits")
            print("   5. Check your internet connection")
        if not test4_result:
            print("   6. Ensure langchain-openai is installed: pip install langchain-openai")
    
    return all_passed


if __name__ == "__main__":
    run_all_openai_tests() 