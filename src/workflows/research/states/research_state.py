from typing import Dict, Any, List, Optional, TypedDict
from pathlib import Path
from src.config import AIConfig, TechSpecConfig

class WorkflowState(TypedDict, total=False):
    """State representation for the research workflow."""
    config : AIConfig
    techSpecConfig: TechSpecConfig

    connector_name: str
    output_dir: Path
    test_only: bool
    verbose: bool
    generate_techspec: bool
    generate_mockserver: bool