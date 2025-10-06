"""Configuration service."""

import os
import subprocess
import json
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from dotenv import load_dotenv

from research_types import ResearchConfig, AIConfig


class ConfigService:
    """Configuration management service."""

    _instance: Optional['ConfigService'] = None

    def __init__(self):
        """Initialize configuration service."""
        # Load environment variables
        load_dotenv()

        # Initialize research config
        self.research_config = ResearchConfig(
            max_depth=int(os.getenv('MAX_DEPTH', '10')),
            max_pages_per_depth=int(os.getenv('MAX_PAGES_PER_DEPTH', '10')),
            max_total_pages=int(os.getenv('MAX_TOTAL_PAGES', '100')),
            max_concurrent_pages=int(os.getenv('CONCURRENT_PAGES', '3')),
            link_relevance_threshold=float(os.getenv('LINK_RELEVANCE_THRESHOLD', '0.2')),
            timeout_per_page=int(os.getenv('TIMEOUT_PER_PAGE_MS', '30000')),
            respect_robots_txt=os.getenv('RESPECT_ROBOTS_TXT', 'true').lower() != 'false',
            data_directory=os.getenv('RESEARCH_DATA_DIR', './research_data'),
            history_file=os.getenv('HISTORY_FILE', './research_history.json'),
            interactive_mode=os.getenv('INTERACTIVE_MODE', 'true').lower() != 'false',
            enable_deep_link_crawling=os.getenv('ENABLE_DEEP_LINK_CRAWLING', 'true').lower() != 'false',
            max_links_per_page=int(os.getenv('MAX_LINKS_PER_PAGE', '10')),
            deep_crawl_depth=int(os.getenv('DEEP_CRAWL_DEPTH', '10')),
            ai_driven_crawling=os.getenv('AI_DRIVEN_CRAWLING', 'false').lower() == 'true',
            ai_link_ranking=os.getenv('AI_LINK_RANKING', 'false').lower() == 'true',
            ai_completeness_check=os.getenv('AI_COMPLETENESS_CHECK', 'false').lower() == 'true',
            search_results_per_query=int(os.getenv('SEARCH_RESULTS_PER_QUERY', '15'))
        )

        # Initialize debug mode
        debug_env = os.getenv('IS_DEBUG', 'false')
        self.debug_mode = debug_env.lower() == 'true' or debug_env == '1'

        # Determine AI provider
        provider_info = self._determine_ai_provider()
        provider = provider_info['provider']
        project_id = provider_info.get('project_id')
        location = provider_info.get('location')
        message = provider_info.get('message')

        # Determine model ID based on provider
        if provider == 'vertex':
            model_id = os.getenv('VERTEX_AI_MODEL') or os.getenv('LITELLM_MODEL_ID') or 'claude-3-5-sonnet-v2@20241022'
        elif provider == 'anthropic':
            model_id = os.getenv('ANTHROPIC_MODEL_ID') or os.getenv('LITELLM_MODEL_ID') or 'claude-3-5-sonnet-20241022'
        else:
            model_id = os.getenv('LITELLM_MODEL_ID', 'gpt-4')

        # Determine API key based on provider
        api_key = None
        if provider == 'anthropic':
            api_key = os.getenv('ANTHROPIC_API_KEY')
        else:
            api_key = os.getenv('LITELLM_API_KEY')

        # Initialize AI config
        self.ai_config = AIConfig(
            provider=provider,
            api_key=api_key,
            base_url=os.getenv('LITELLM_BASE_URL', 'http://localhost:4000/v1'),
            model_id=model_id,
            project_id=project_id or os.getenv('VERTEX_AI_PROJECT_ID'),
            location=location or os.getenv('VERTEX_AI_LOCATION', 'us-east5'),
            custom_instructions_file=os.getenv('CUSTOM_INSTRUCTIONS_FILE'),
            custom_instructions=self._load_custom_instructions(os.getenv('CUSTOM_INSTRUCTIONS_FILE'))
        )

        # Log provider determination
        if message:
            print(message)

    @classmethod
    def get_instance(cls) -> 'ConfigService':
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def is_debug_mode(self) -> bool:
        """Check if debug mode is enabled."""
        return self.debug_mode

    def get_research_config(self) -> ResearchConfig:
        """Get research configuration."""
        return self.research_config

    def get_ai_config(self) -> AIConfig:
        """Get AI configuration."""
        return self.ai_config

    def update_research_config(self, updates: Dict[str, Any]):
        """Update research configuration."""
        for key, value in updates.items():
            if hasattr(self.research_config, key):
                setattr(self.research_config, key, value)

    def update_ai_config(self, updates: Dict[str, Any]):
        """Update AI configuration."""
        for key, value in updates.items():
            if hasattr(self.ai_config, key):
                setattr(self.ai_config, key, value)

    def _determine_ai_provider(self) -> Dict[str, Any]:
        """Intelligently determine which AI provider to use."""
        env_provider = os.getenv('AI_PROVIDER')

        if env_provider == 'litellm':
            if os.getenv('LITELLM_API_KEY'):
                return {'provider': 'litellm'}
            else:
                # Try Vertex AI fallback
                vertex_config = self._check_vertex_ai_availability()
                if vertex_config['available']:
                    return {
                        'provider': 'vertex',
                        'project_id': vertex_config['project_id'],
                        'location': vertex_config['location'],
                        'message': '⚠️  LiteLLM API key not found, falling back to Vertex AI'
                    }
                else:
                    return {'provider': 'litellm'}

        if env_provider == 'vertex':
            vertex_config = self._check_vertex_ai_availability()
            return {
                'provider': 'vertex',
                'project_id': vertex_config.get('project_id'),
                'location': vertex_config.get('location'),
                'message': None if vertex_config['available'] else '⚠️  Vertex AI configuration incomplete'
            }

        # No explicit provider set, try intelligent detection
        if os.getenv('LITELLM_API_KEY'):
            return {'provider': 'litellm'}

        vertex_config = self._check_vertex_ai_availability()
        if vertex_config['available']:
            return {
                'provider': 'vertex',
                'project_id': vertex_config['project_id'],
                'location': vertex_config['location'],
                'message': '🔍 No LiteLLM API key found, using Vertex AI'
            }

        # Default to LiteLLM
        return {'provider': 'litellm'}

    def _check_vertex_ai_availability(self) -> Dict[str, Any]:
        """Check Vertex AI availability with multiple fallback methods."""
        # Method 1: Check environment variables
        if os.getenv('VERTEX_AI_PROJECT_ID'):
            return {
                'available': True,
                'project_id': os.getenv('VERTEX_AI_PROJECT_ID'),
                'location': os.getenv('VERTEX_AI_LOCATION', 'us-central1')
            }

        # Method 2: Check Google Cloud SDK configuration
        try:
            result = subprocess.run(
                ['gcloud', 'config', 'get-value', 'project'],
                capture_output=True,
                text=True,
                timeout=5
            )
            project_id = result.stdout.strip()

            if project_id and project_id != '(unset)' and project_id != '':
                return {
                    'available': True,
                    'project_id': project_id,
                    'location': 'us-central1'
                }
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            pass

        # Method 3: Check Application Default Credentials
        adc_paths = [
            os.getenv('GOOGLE_APPLICATION_CREDENTIALS'),
            os.path.expanduser('~/.config/gcloud/application_default_credentials.json'),
            os.path.expanduser('~/AppData/Roaming/gcloud/application_default_credentials.json')
        ]

        for path in adc_paths:
            if path and Path(path).exists():
                try:
                    with open(path, 'r') as f:
                        credentials = json.load(f)
                        project_id = credentials.get('project_id') or credentials.get('quota_project_id')
                        if project_id:
                            return {
                                'available': True,
                                'project_id': project_id,
                                'location': 'us-central1'
                            }
                except (json.JSONDecodeError, IOError):
                    pass

        return {'available': False}

    def _load_custom_instructions(self, file_path: Optional[str]) -> Optional[str]:
        """Load custom instructions from file."""
        if not file_path:
            return None

        try:
            resolved_path = Path(file_path).resolve()
            if not resolved_path.exists():
                print(f'Custom instructions file not found: {resolved_path}')
                return None

            instructions = resolved_path.read_text(encoding='utf-8').strip()
            if not instructions:
                print(f'Custom instructions file is empty: {resolved_path}')
                return None

            print(f'Loaded custom instructions from: {resolved_path} ({len(instructions)} characters)')
            return instructions
        except Exception as e:
            print(f'Error loading custom instructions from {file_path}: {e}')
            return None

    def reload_custom_instructions(self):
        """Reload custom instructions from file."""
        self.ai_config.custom_instructions = self._load_custom_instructions(
            self.ai_config.custom_instructions_file
        )

    def validate(self) -> List[str]:
        """Validate configuration."""
        errors = []

        # Validate AI provider configuration
        if self.ai_config.provider == 'litellm':
            if not self.ai_config.api_key:
                errors.append('LITELLM_API_KEY is required when using litellm provider')
                errors.append('To fix: Add LITELLM_API_KEY to your .env file')
                errors.append('Or set AI_PROVIDER=vertex in .env to use Vertex AI instead')

        if self.ai_config.provider == 'vertex':
            if not self.ai_config.project_id:
                errors.append('Vertex AI project ID is required when using vertex provider')
                errors.append('To fix: Set VERTEX_AI_PROJECT_ID in .env or configure gcloud CLI')

        # Validate research configuration
        if self.research_config.max_depth < 1 or self.research_config.max_depth > 10:
            errors.append('MAX_DEPTH must be between 1 and 10')

        if self.research_config.max_concurrent_pages < 1 or self.research_config.max_concurrent_pages > 10:
            errors.append('CONCURRENT_PAGES must be between 1 and 10')

        # Validate custom instructions file if specified
        if self.ai_config.custom_instructions_file:
            resolved_path = Path(self.ai_config.custom_instructions_file).resolve()
            if not resolved_path.exists():
                errors.append(f'Custom instructions file not found: {resolved_path}')

        return errors
