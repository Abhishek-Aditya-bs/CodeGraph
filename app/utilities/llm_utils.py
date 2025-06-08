# Code Graph - LLM Utilities
# Utility functions for LLM context preparation and response generation

import logging
from typing import List, Dict, Tuple
from app.config import Config

logger = logging.getLogger(__name__)
config = Config()


def prepare_context_for_llm(query: str, vector_results: List[Dict], graph_context: Dict) -> Dict:
    """
    Prepare structured context data for LLM prompt
    
    Args:
        query: User's original query
        vector_results: Vector search results
        graph_context: Graph traversal context
        
    Returns:
        Dict: Organized context for LLM
    """
    # Organize code chunks
    code_chunks = []
    for i, result in enumerate(vector_results[:3], 1):  # Top 3 most relevant
        file_name = result['file_path'].split('/')[-1] if '/' in result['file_path'] else result['file_path']
        
        # Clean and truncate code for better LLM processing
        code_text = result['text']
        if len(code_text) > 1000:
            # Find a good breaking point
            break_point = code_text.rfind('\n', 0, 1000)
            if break_point > 800:
                code_text = code_text[:break_point] + "\n... (truncated for brevity)"
            else:
                code_text = code_text[:1000] + "..."
        
        code_chunks.append({
            'rank': i,
            'file_name': file_name,
            'file_path': result['file_path'],
            'language': result['language'],
            'lines': f"{result['start_line']}-{result['end_line']}",
            'similarity': f"{result['similarity_score']:.3f}",
            'code': code_text
        })
    
    # Organize entities
    entities_by_type = {}
    for entity in graph_context.get('entities', []):
        entity_type = entity['type']
        if entity_type not in entities_by_type:
            entities_by_type[entity_type] = []
        entities_by_type[entity_type].append(entity['id'])
    
    # Organize relationships
    relationships_by_type = {}
    for rel in graph_context.get('relationships', []):
        rel_type = rel['relationship']
        if rel_type not in relationships_by_type:
            relationships_by_type[rel_type] = []
        relationships_by_type[rel_type].append(f"{rel['source']} → {rel['target']}")
    
    # File summary
    files_summary = []
    for file_info in graph_context.get('files', [])[:3]:  # Top 3 files
        files_summary.append({
            'name': file_info['name'],
            'language': file_info['language'],
            'entity_count': file_info['entity_count'],
            'entity_types': file_info['entity_types']
        })
    
    return {
        'query': query,
        'total_chunks': len(vector_results),
        'total_files': len(set(r['file_path'] for r in vector_results)),
        'code_chunks': code_chunks,
        'entities': entities_by_type,
        'relationships': relationships_by_type,
        'files': files_summary
    }


def create_conversational_prompt(context_data: Dict) -> str:
    """
    Create a comprehensive prompt for conversational response generation
    
    Args:
        context_data: Organized context data
        
    Returns:
        str: Formatted prompt for LLM
    """
    prompt_parts = []
    
    # User query context
    prompt_parts.append(f"The user asked: \"{context_data['query']}\"")
    prompt_parts.append(f"\nI found {context_data['total_chunks']} relevant code chunks across {context_data['total_files']} files.")
    
    # Most relevant code
    prompt_parts.append("\nMost relevant code found:")
    for chunk in context_data['code_chunks']:
        prompt_parts.append(f"\n{chunk['rank']}. File: {chunk['file_name']} (Lines {chunk['lines']}, {chunk['language']})")
        prompt_parts.append(f"Code:\n```{chunk['language']}\n{chunk['code']}\n```")
    
    # Entities and relationships context
    if context_data['entities']:
        prompt_parts.append("\nCode entities found:")
        for entity_type, entity_list in context_data['entities'].items():
            prompt_parts.append(f"- {entity_type}s: {', '.join(entity_list[:5])}")
    
    if context_data['relationships']:
        prompt_parts.append("\nCode relationships:")
        for rel_type, rel_list in context_data['relationships'].items():
            prompt_parts.append(f"- {rel_type}: {', '.join(rel_list[:3])}")
    
    # Files context
    if context_data['files']:
        prompt_parts.append("\nKey files involved:")
        for file_info in context_data['files']:
            prompt_parts.append(f"- {file_info['name']} ({file_info['language']}) with {file_info['entity_count']} entities")
    
    prompt_parts.append("\nPlease provide a helpful, conversational explanation of what you found. Focus on answering the user's question in a natural way, explaining the code and its relationships. Be specific about what the code does and how the components work together.")
    
    return "\n".join(prompt_parts)


def generate_fallback_response(vector_results: List[Dict], graph_context: Dict) -> str:
    """
    Generate a simple fallback response if LLM fails
    
    Args:
        vector_results: Vector search results
        graph_context: Graph context
        
    Returns:
        str: Simple fallback response
    """
    file_names = [r['file_path'].split('/')[-1] for r in vector_results[:3]]
    
    response = f"I found {len(vector_results)} relevant code chunks that might help with your question. "
    response += f"The most relevant files are: {', '.join(file_names)}. "
    
    if graph_context.get('entities'):
        entity_count = len(graph_context['entities'])
        response += f"These files contain {entity_count} related code entities including classes and functions. "
    
    response += "You might want to explore these files to find what you're looking for."
    
    return response


def generate_conversational_response(context_data: Dict, openai_api_key: str) -> Tuple[bool, str]:
    """
    Use LLM to generate a natural, conversational response
    
    Args:
        context_data: Organized context for the LLM
        openai_api_key: OpenAI API key
        
    Returns:
        Tuple[bool, str]: (success, conversational_response)
    """
    try:
        from openai import OpenAI
        
        client = OpenAI(api_key=openai_api_key)
        
        # Create comprehensive prompt for conversational response
        prompt = create_conversational_prompt(context_data)
        
        response = client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": """You are a helpful AI coding assistant that explains code in a natural, conversational way. 
                    
                    Your responses should be:
                    - Conversational and friendly
                    - Technically accurate but easy to understand
                    - Focused on helping developers understand code
                    - Include relevant code snippets when helpful
                    - Explain relationships between code components
                    - Suggest next steps or related areas to explore
                    
                    Avoid:
                    - Overly formal or structured language
                    - Repeating the user's question
                    - Generic responses
                    - Bullet points or formal sections"""
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        conversational_response = response.choices[0].message.content.strip()
        return True, conversational_response
        
    except Exception as e:
        logger.error(f"LLM response generation failed: {str(e)}")
        return False, "" 