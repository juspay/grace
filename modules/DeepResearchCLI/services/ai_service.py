"""AI service for LLM interactions."""

import json
import re
import os
from typing import List, Dict, Any, Optional, Tuple
import httpx

from research_types import AIConfig, AIMessage, AIResponse
from utils.debug_logger import DebugLogger


class AIConfigurationError(Exception):
    """AI configuration error with help message."""

    def __init__(self, message: str, config_help: str):
        super().__init__(message)
        self.config_help = config_help


class AIService:
    """Service for AI/LLM interactions."""

    def __init__(self, config: AIConfig):
        """Initialize AI service.

        Args:
            config: AI configuration
        """
        self.config = config
        self.debug_logger = DebugLogger.get_instance()

    def _clean_json_response(self, content: str) -> str:
        """Clean AI response to extract valid JSON.

        Args:
            content: Raw response content

        Returns:
            Cleaned JSON string
        """
        # Remove markdown code blocks
        cleaned = re.sub(r'```json\s*\n?', '', content, flags=re.IGNORECASE)
        cleaned = re.sub(r'```javascript\s*\n?', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'```\s*\n?', '', cleaned)
        cleaned = re.sub(r'```\s*$', '', cleaned)

        # Remove leading/trailing whitespace
        cleaned = cleaned.strip()

        # Find JSON start
        json_start = re.search(r'[\{\[]', cleaned)
        if json_start:
            cleaned = cleaned[json_start.start():]

        # Find last valid closing brace/bracket
        brace_count = 0
        bracket_count = 0
        last_valid_index = -1

        for i, char in enumerate(cleaned):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
            elif char == '[':
                bracket_count += 1
            elif char == ']':
                bracket_count -= 1

            if brace_count == 0 and bracket_count == 0 and char in '}]':
                last_valid_index = i
                break

        if last_valid_index > -1:
            cleaned = cleaned[:last_valid_index + 1]

        return cleaned

    def _enhance_messages_with_custom_instructions(
        self,
        messages: List[AIMessage]
    ) -> List[AIMessage]:
        """Enhance messages with custom instructions.

        Args:
            messages: Original messages

        Returns:
            Enhanced messages
        """
        if not self.config.custom_instructions:
            return messages

        enhanced_messages = messages.copy()

        # Find system message or create one
        system_msg_idx = next(
            (i for i, msg in enumerate(enhanced_messages) if msg.role == 'system'),
            None
        )

        if system_msg_idx is not None:
            # Prepend custom instructions
            enhanced_messages[system_msg_idx] = AIMessage(
                role='system',
                content=f"Custom Instructions to follow: {self.config.custom_instructions}\n\n{enhanced_messages[system_msg_idx].content}"
            )
        else:
            # Add new system message
            enhanced_messages.insert(0, AIMessage(
                role='system',
                content=self.config.custom_instructions
            ))

        return enhanced_messages

    def get_custom_instructions_info(self) -> Dict[str, Any]:
        """Get custom instructions information."""
        return {
            'has_custom_instructions': bool(self.config.custom_instructions),
            'instructions_length': len(self.config.custom_instructions) if self.config.custom_instructions else 0,
            'file_path': self.config.custom_instructions_file
        }

    async def generate_text(
        self,
        messages: List[AIMessage],
        temperature: float = 0.3,
        max_tokens: int = 4096
    ) -> AIResponse:
        """Generate text using AI.

        Args:
            messages: Conversation messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            AI response

        Raises:
            AIConfigurationError: If configuration is invalid
        """
        try:
            # Enhance messages
            enhanced_messages = self._enhance_messages_with_custom_instructions(messages)

            if self.config.provider == 'litellm':
                return await self._call_litellm(enhanced_messages, temperature, max_tokens)
            elif self.config.provider == 'vertex':
                return await self._call_vertex_ai(enhanced_messages, temperature, max_tokens)
            elif self.config.provider == 'anthropic':
                return await self._call_anthropic_direct(enhanced_messages, temperature, max_tokens)
            else:
                raise AIConfigurationError(
                    f"Unsupported AI provider: {self.config.provider}",
                    self._get_config_help()
                )

        except AIConfigurationError:
            raise
        except Exception as error:
            error_msg = str(error)

            if '401' in error_msg or 'Unauthorized' in error_msg:
                raise AIConfigurationError("Invalid API key", self._get_config_help())
            if 'ECONNREFUSED' in error_msg or 'network' in error_msg.lower():
                raise AIConfigurationError("Cannot connect to AI service", self._get_config_help())
            if 'timeout' in error_msg.lower():
                raise AIConfigurationError("AI service timeout", self._get_timeout_help())

            raise AIConfigurationError(
                f"AI service error: {error_msg}",
                self._get_config_help()
            )

    async def test_connection(self) -> Dict[str, Any]:
        """Test AI service connection."""
        try:
            test_messages = [
                AIMessage(
                    role='user',
                    content='Reply with exactly "TEST_OK" if you can process this message.'
                )
            ]

            response = await self.generate_text(test_messages, temperature=0, max_tokens=10)

            if 'TEST_OK' in response.content:
                return {'success': True}
            else:
                return {
                    'success': False,
                    'error': 'AI service responded but response format was unexpected',
                    'config_help': self._get_config_help()
                }

        except AIConfigurationError as error:
            return {
                'success': False,
                'error': str(error),
                'config_help': error.config_help
            }
        except Exception as error:
            return {
                'success': False,
                'error': str(error),
                'config_help': self._get_config_help()
            }

    def _get_config_help(self) -> str:
        """Get configuration help message."""
        return """
AI Configuration Help:

1. Check your .env file:
   - LITELLM_API_KEY=your_api_key_here
   - LITELLM_BASE_URL=https://grid.ai.juspay.net
   - LITELLM_MODEL_ID=qwen3-coder-480b

2. Ensure LiteLLM server is running:
   - Start LiteLLM: litellm --config config.yaml
   - Test connection: curl http://localhost:4000/health

3. Verify API key is valid:
   - Check if API key has sufficient credits
   - Ensure API key has correct permissions

4. Alternative providers:
   - Set AI_PROVIDER=vertex for Google Vertex AI
   - Configure VERTEX_AI_PROJECT_ID and VERTEX_AI_LOCATION

📚 For more help, see: https://docs.litellm.ai/
"""

    def _get_timeout_help(self) -> str:
        """Get timeout help message."""
        return """
AI Timeout Configuration Help:
- Ensure AI service is responsive
- Increase timeout value if necessary
For more help, see: https://docs.litellm.ai/
"""

    async def _call_litellm(
        self,
        messages: List[AIMessage],
        temperature: float,
        max_tokens: int
    ) -> AIResponse:
        """Call LiteLLM API."""
        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                f"{self.config.base_url}/chat/completions",
                json={
                    'model': self.config.model_id,
                    'messages': [{'role': msg.role, 'content': msg.content} for msg in messages],
                    'temperature': temperature,
                    'max_tokens': max_tokens,
                    'stream': False
                },
                headers={
                    'Authorization': f"Bearer {self.config.api_key}",
                    'Content-Type': 'application/json'
                }
            )

        result = response.json()
        return AIResponse(
            content=result['choices'][0]['message']['content'],
            tokens_used=result.get('usage', {}).get('total_tokens', 0)
        )

    async def _call_vertex_ai(
        self,
        messages: List[AIMessage],
        temperature: float,
        max_tokens: int
    ) -> AIResponse:
        """Call Vertex AI."""
        from google.auth import default
        from google.auth.transport.requests import Request

        model_id = self.config.model_id or 'claude-sonnet-4-5@20250929'

        if 'claude' in model_id or 'anthropic' in model_id:
            return await self._call_vertex_anthropic_sdk(messages, temperature, max_tokens)
        else:
            return await self._call_vertex_gemini(messages, temperature, max_tokens)

    async def _call_vertex_anthropic_sdk(
        self,
        messages: List[AIMessage],
        temperature: float,
        max_tokens: int
    ) -> AIResponse:
        """Call Vertex AI with Anthropic models."""
        from anthropic import AnthropicVertex

        client = AnthropicVertex(
            project_id=self.config.project_id,
            region=self.config.location or 'us-east5'
        )

        # Convert messages
        anthropic_messages = [
            {'role': msg.role, 'content': msg.content}
            for msg in messages
            if msg.role != 'system'
        ]

        system_message = next(
            (msg.content for msg in messages if msg.role == 'system'),
            None
        )

        kwargs = {
            'model': self.config.model_id,
            'max_tokens': max_tokens,
            'temperature': temperature,
            'messages': anthropic_messages
        }

        if system_message:
            kwargs['system'] = system_message

        response = client.messages.create(**kwargs)

        text_content = next(
            (block.text for block in response.content if block.type == 'text'),
            ''
        )

        return AIResponse(
            content=text_content,
            tokens_used=response.usage.input_tokens + response.usage.output_tokens
        )

    async def _call_vertex_gemini(
        self,
        messages: List[AIMessage],
        temperature: float,
        max_tokens: int
    ) -> AIResponse:
        """Call Vertex AI with Gemini models."""
        from google.auth import default
        from google.auth.transport.requests import Request

        credentials, project = default()
        credentials.refresh(Request())

        # Convert messages to Gemini format
        contents = []
        system_instruction = None

        for message in messages:
            if message.role == 'system':
                system_instruction = message.content
            else:
                contents.append({
                    'role': 'model' if message.role == 'assistant' else 'user',
                    'parts': [{'text': message.content}]
                })

        request_body = {
            'contents': contents,
            'generationConfig': {
                'temperature': temperature,
                'maxOutputTokens': max_tokens,
                'topP': 0.8,
                'topK': 40
            }
        }

        if system_instruction:
            request_body['systemInstruction'] = {
                'parts': [{'text': system_instruction}]
            }

        location = self.config.location or 'us-central1'
        url = f"https://{location}-aiplatform.googleapis.com/v1/projects/{project}/locations/{location}/publishers/google/models/{self.config.model_id}:generateContent"

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                url,
                json=request_body,
                headers={
                    'Authorization': f"Bearer {credentials.token}",
                    'Content-Type': 'application/json'
                }
            )

        result = response.json()
        content = result['candidates'][0]['content']['parts'][0]['text']
        tokens_used = result.get('usageMetadata', {}).get('totalTokenCount', 0)

        return AIResponse(content=content, tokens_used=tokens_used)

    async def _call_anthropic_direct(
        self,
        messages: List[AIMessage],
        temperature: float,
        max_tokens: int
    ) -> AIResponse:
        """Call Anthropic API directly."""
        from anthropic import Anthropic

        if not self.config.api_key:
            raise Exception("Anthropic API key is required. Set ANTHROPIC_API_KEY in your .env file.")

        client = Anthropic(api_key=self.config.api_key)

        # Convert messages
        anthropic_messages = [
            {'role': msg.role, 'content': msg.content}
            for msg in messages
            if msg.role != 'system'
        ]

        system_message = next(
            (msg.content for msg in messages if msg.role == 'system'),
            None
        )

        kwargs = {
            'model': self.config.model_id or 'claude-3-5-sonnet-20241022',
            'max_tokens': max_tokens,
            'temperature': temperature,
            'messages': anthropic_messages
        }

        if system_message:
            kwargs['system'] = system_message

        response = client.messages.create(**kwargs)

        text_content = next(
            (block.text for block in response.content if block.type == 'text'),
            ''
        )

        return AIResponse(
            content=text_content,
            tokens_used=response.usage.input_tokens + response.usage.output_tokens
        )

    async def generate_search_queries(
        self,
        original_query: str,
        depth: int,
        previous_results: Optional[List[str]] = None
    ) -> List[str]:
        """Generate search queries for research.

        Args:
            original_query: Original research query
            depth: Current depth level
            previous_results: Previous search results

        Returns:
            List of search queries
        """
        system_prompt = """Generate 2-5 search queries to find comprehensive information about the topic.
The queries should be diverse and explore different aspects of the topic.
Return as a JSON array of strings. Also check with more specific domain related queries.
Try to ignore social media links and programming language docs links except related to the custom instructions topics."""

        if depth > 1:
            system_prompt += f" This is depth level {depth}, so focus on more specific and detailed aspects."

        user_content = f'Original query: "{original_query}"\n\n'
        if previous_results:
            user_content += f"Previous results context: {', '.join(previous_results)}\n\n"
        user_content += "Generate search queries:"

        messages = [
            AIMessage(role='system', content=system_prompt),
            AIMessage(role='user', content=user_content)
        ]

        try:
            response = await self.generate_text(messages, temperature=0.7, max_tokens=200)
            cleaned = self._clean_json_response(response.content)

            if not cleaned or len(cleaned) < 2:
                return [original_query]

            queries = json.loads(cleaned)
            return queries if isinstance(queries, list) else [original_query]
        except Exception as error:
            print(f"Warning: Failed to generate search queries: {error}")
            return [original_query]

    async def analyze_search_results(
        self,
        query: str,
        results: List[Dict[str, str]]
    ) -> List[str]:
        """Analyze search results and return relevant URLs.

        Args:
            query: Search query
            results: Search results

        Returns:
            List of relevant URLs
        """
        if not results:
            return []

        system_prompt = f"""You are a search results analyzer.
Summarize the key findings from the search results that are relevant to the query.
Ignore the duplicate links.
Try to ignore social media links and programming language docs links except related to the custom instructions topics.
Also you have to remember that relevance should be related to this custom instruction topics customInstructions: {self.config.custom_instructions or "N/A"}

Query: "{query}"

Top Search Results: {chr(10).join([f'{idx + 1}. {res.get("title")} - {res.get("snippet")} (url: {res.get("url")})' for idx, res in enumerate(results)])}

Return as a JSON array of relevant url links from provided search results.
["url1", "url2"] from the given list of search results.
"""

        messages = [
            AIMessage(role='system', content=system_prompt),
            AIMessage(role='user', content=f'Analyze the search results for the query: "{query}"\n\nProvide a summary of key findings:\nReturn as a JSON array of relevant url links from provided search results.\n["url1", "url2"] from the given list of search results.')
        ]

        try:
            response = await self.generate_text(messages, temperature=0.3, max_tokens=500)
            cleaned = self._clean_json_response(response.content)
            insights = json.loads(cleaned)
            return insights if isinstance(insights, list) else []
        except Exception as error:
            print(f"Warning: Failed to analyze search results: {error}")
            return []

    async def synthesize_results(
        self,
        query: str,
        all_content: List[Dict[str, Any]],
        isChunked: bool = False
    ) -> Dict[str, Any]:
        """Synthesize research results into final answer.

        Args:
            query: Research query
            all_content: All collected content

        Returns:
            Dict with answer, confidence, and summary
        """
        sorted_content = sorted(all_content, key=lambda x: x.get('relevance_score', 0.5), reverse=True)

        has_custom_instructions = bool(
            self.config.custom_instructions and self.config.custom_instructions.strip()
        )

        if has_custom_instructions:
            system_prompt = f"""You are an expert research analyst. Based on the collected research data, provide a comprehensive analysis following the custom format requirements that will be provided.
Also you have to give the confidence which will satisfy this regex: 'confidence[:\\s]+([0-9.]+)'
Also you have to give the summary which will satisfy this regex: '(?:summary|executive summary)[:\\s]*([^\\n]{{50,200}})'

Important: The custom instructions contain the specific output format and requirements. Follow them exactly.

Research Guidelines:
1. Analyze all provided data thoroughly
2. Extract relevant information for the requested format
3. Ensure accuracy and completeness
4. Include source references where applicable
5. Maintain high attention to detail

{ isChunked and "The data provided by user is actually a chunked data. So you have to consider that while synthesizing the results."}
"""
        else:
            system_prompt = """You are an expert research analyst. Provide a comprehensive, well-structured answer based on the research data.

Requirements:
1. Start with a clear summary
2. Organize information logically
3. Include specific details and evidence
4. Cite sources when relevant
5. End with key takeaways

Format:
SUMMARY: [2-3 sentence overview]

DETAILED ANALYSIS:
[Comprehensive findings organized by topic]

KEY POINTS:
- [Main finding 1]
- [Main finding 2]
- [Main finding 3]

CONFIDENCE: [0.0-1.0 confidence score]
{ isChunked and "The data provided by user is actually a chunked data. So you have to consider that while synthesizing the results."}
"""

        content_summary =[
            f"[{idx + 1}] {item.get('title', 'Unknown')} (Relevance: {item.get('relevance_score', 0.5):.2f})\nURL: {item.get('url', 'N/A')}\nContent: {item.get('content', '')[:500]}..."
            for idx, item in enumerate(sorted_content[:20])
        ]

        messages = [
            AIMessage(role='system', content=system_prompt),
            *[AIMessage(role="user", content=f"source {idx} : {insight}" ) for idx, insight in enumerate(content_summary)],
        ]

        try:
            response = await self.generate_text(messages, temperature=0.5, max_tokens=8000)

            # Extract confidence
            confidence_match = re.search(r'confidence[:\s]+([0-9.]+)', response.content, re.IGNORECASE)
            confidence = float(confidence_match.group(1)) if confidence_match else 0.7

            # Extract summary
            summary_match = re.search(r'(?:summary|executive summary)[:\s]*([^\n]{50,200})', response.content, re.IGNORECASE)
            summary = summary_match.group(1).strip() if summary_match else response.content[:200]

            return {
                'answer': response.content,
                'confidence': max(0.0, min(1.0, confidence)),
                'summary': summary
            }
        except Exception as error:
            print(f"Warning: Failed to synthesize results: {error}")
            return {
                'answer': f"Research completed for: {query}\n\nData collected from {len(all_content)} sources.",
                'confidence': 0.5,
                'summary': f"Research on {query}"
            }

    async def generate_link_quality_prompt(
        self,
        custom_instructions: str,
        query: str
    ) -> str:
        """Generate link quality evaluation prompt from custom instructions."""
        messages = [
            AIMessage(
                role='system',
                content="Generate a concise quality criteria (1-2 sentences) for evaluating web links based on custom instructions."
            ),
            AIMessage(
                role='user',
                content=f"Custom Instructions:\n{custom_instructions}\n\nQuery: {query}\n\nGenerate link quality criteria:"
            )
        ]

        try:
            response = await self.generate_text(messages, temperature=0.3, max_tokens=100)
            return response.content.strip()
        except Exception:
            return "Links should be relevant and authoritative for the research topic."

    async def filter_links_by_quality(
        self,
        links: List[Dict[str, str]],
        quality_prompt: str,
        query: str
    ) -> List[Dict[str, str]]:
        """Filter links by quality using AI."""
        if not links:
            return []

        links_text = "\n".join([
            f"{idx + 1}. {link.get('text', 'Unknown')} ({link.get('url', 'N/A')})"
            for idx, link in enumerate(links[:20])
        ])

        messages = [
            AIMessage(
                role='system',
                content=f"Filter links based on quality criteria: {quality_prompt}\nReturn indices of quality links as JSON array: [1, 3, 5]"
            ),
            AIMessage(
                role='user',
                content=f"Query: {query}\n\nLinks:\n{links_text}\n\nReturn quality link indices:"
            )
        ]

        try:
            response = await self.generate_text(messages, temperature=0.2, max_tokens=200)
            cleaned = self._clean_json_response(response.content)
            indices = json.loads(cleaned)

            if isinstance(indices, list):
                return [links[i - 1] for i in indices if 0 < i <= len(links)]
            return links
        except Exception:
            return links

    async def rank_links_for_crawling(
        self,
        query: str,
        links: List[Dict[str, str]],
        current_context: str
    ) -> List[Dict[str, Any]]:
        """Rank links for crawling using AI."""
        if not links:
            return []

        links_text = "\n\n".join([
            f"{idx + 1}. {link.get('text', 'Unknown')} ({link.get('url', 'N/A')})\n   Context: {link.get('context', 'N/A')[:100]}"
            for idx, link in enumerate(links[:20])
        ])

        system_prompt = """You are a research url link evaluator.
Score each link's potential value for the research query based on the relevance provided by the custom instructions if provided.

Return JSON array with this format:
[
  {"index": 1, "score": 0.9, "reason": "Directly addresses main topic"},
  {"index": 2, "score": 0.3, "reason": "Tangentially related"}
]

Score 0.0-1.0 based on:
- Relevance to query
- Likely information quality
- Uniqueness (avoid redundant sources)"""

        messages = [
            AIMessage(role='system', content=system_prompt),
            AIMessage(role='user', content=f"Custom Instructions: {self.config.custom_instructions or 'N/A'}"),
            AIMessage(role='user', content=f"Research Query: \"{query}\"\n\nCurrent Context: {current_context}\n\nLinks to Evaluate:\n{links_text}\n\nRank these links")
        ]

        try:
            response = await self.generate_text(messages, temperature=0.2, max_tokens=1000)
            cleaned = self._clean_json_response(response.content)
            rankings = json.loads(cleaned)

            if not isinstance(rankings, list):
                raise ValueError("Invalid rankings format")

            ranked_links = [
                {
                    'url': links[r['index'] - 1]['url'],
                    'score': max(0.0, min(1.0, r.get('score', 0.5))),
                    'reason': r.get('reason', '')
                }
                for r in rankings
                if 'index' in r and 0 < r['index'] <= len(links)
            ]

            return sorted(ranked_links, key=lambda x: x['score'], reverse=True)
        except Exception as error:
            print(f"Warning: Failed to rank links: {error}")
            return [{'url': link['url'], 'score': 0.5, 'reason': 'AI ranking failed'} for link in links]

    async def should_continue_crawling(
        self,
        query: str,
        current_depth: int,
        max_depth: int,
        pages_collected: int,
        current_insights: List[str]
    ) -> Dict[str, Any]:
        """Determine if crawling should continue."""
        messages = [
            AIMessage(
                role='system',
                content="""You are a research strategist. Decide if we should continue crawling deeper for more information.
Consider: information completeness, depth vs quality trade-off, and whether we have enough data.

Respond in JSON format:
{
  "shouldContinue": true/false,
  "reason": "Brief explanation (1 sentence)",
  "confidence": 0.0-1.0
}"""
            ),
            *[AIMessage(role="user", content=f"source {idx} : {insight}" ) for idx, insight in enumerate(current_insights[:10])],
            AIMessage(
                role='user',
                content=f"""Research Query: "{query}"
Current Status:
- Depth: {current_depth}/{max_depth}
- Pages Collected: {pages_collected}
- Key Insights Found: {len(current_insights) if current_insights else 0}

Should we continue to depth {current_depth + 1}?"""
            )
        ]

        try:
            response = await self.generate_text(messages, temperature=0.3, max_tokens=150)
            cleaned = self._clean_json_response(response.content)
            result = json.loads(cleaned)

            return {
                'shouldContinue': result.get('shouldContinue', True),
                'reason': result.get('reason', 'No reason provided'),
                'confidence': max(0.0, min(1.0, result.get('confidence', 0.5)))
            }
        except Exception:
            return {
                'shouldContinue': current_depth < max_depth,
                'reason': 'AI decision failed, using depth limit',
                'confidence': 0.5
            }

    async def assess_information_completeness(
        self,
        query: str,
        pages_collected: int,
        insights: List[str]
    ) -> Dict[str, Any]:
        """Assess if collected information is complete."""
        has_custom_instructions = bool(
            self.config.custom_instructions and self.config.custom_instructions.strip()
        )

        system_content = "You are a research completeness evaluator. Assess if we have enough information to comprehensively answer the query."

        if has_custom_instructions:
            system_content += f"\n\nIMPORTANT: Also check if we have gathered sufficient information to meet the CUSTOM INSTRUCTIONS requirements.\ncustomInstructions: {self.config.custom_instructions}"

        system_content += """\n\nRespond in JSON:
{
  "isComplete": true/false,
  "missingAspects": ["aspect1", "aspect2"],
  "confidence": 0.0-1.0"""

        if has_custom_instructions:
            system_content += ',\n  "customInstructionsMet": true/false'

        system_content += "\n}"

        messages = [
            AIMessage(role='system', content=system_content),
            AIMessage(role='assistant', content=f"Pages Collected: {pages_collected}")
        ]

        for idx, insight in enumerate(insights[:10]):
            messages.append(AIMessage(role='assistant', content=f"Source {idx + 1}: {insight}"))

        messages.append(AIMessage(
            role='user',
            content=f'Research Query: "{query}"\nIs this information sufficient? Respond in JSON.'
        ))

        try:
            response = await self.generate_text(messages, temperature=0.3, max_tokens=300)
            cleaned = self._clean_json_response(response.content)
            result = json.loads(cleaned)

            return {
                'isComplete': result.get('isComplete', False),
                'missingAspects': result.get('missingAspects', []) if isinstance(result.get('missingAspects'), list) else [],
                'confidence': max(0.0, min(1.0, result.get('confidence', 0.5))),
                'customInstructionsMet': result.get('customInstructionsMet') if has_custom_instructions else None
            }
        except Exception as error:
            print(f"Warning: Failed to assess completeness: {error}")
            return {
                'isComplete': False,
                'missingAspects': [],
                'confidence': 0.3,
                'customInstructionsMet': False if has_custom_instructions else None
            }

    async def generate_named_description(self, query: str) -> str:
        """Generate a short name/description for the query."""
        messages = [
            AIMessage(
                role='system',
                content="Generate a short filename-safe name (1-2 words, no spaces, use hyphens) add the query in single word for this research query."
            ),
            AIMessage(role='user', content=f'Query: "{query}"\n\nGenerate name:')
        ]

        try:
            response = await self.generate_text(messages, temperature=0.3, max_tokens=20)
            name = response.content.strip().replace(' ', '-').replace('_', '-')
            # Remove special characters
            name = re.sub(r'[^a-zA-Z0-9-]', '', name)
            return name[:50] if name else 'research'
        except Exception:
            return 'research'
