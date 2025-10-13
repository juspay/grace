"""Base workflow infrastructure for Grace CLI workflows."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, TypedDict, List, cast
from dataclasses import dataclass
from enum import Enum
import asyncio
import time
import json
from datetime import datetime, timezone


class WorkflowStatus(Enum):
    """Standard workflow execution statuses."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowStepStatus(Enum):
    """Status for individual workflow steps."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowMetadata:
    """Metadata for workflow execution."""
    workflow_id: str
    workflow_type: str
    status: WorkflowStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    steps_completed: int = 0
    total_steps: int = 0
    error_message: Optional[str] = None
    tags: Optional[Dict[str, str]] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = {}


@dataclass
class WorkflowStep:
    """Represents a single step in a workflow."""
    name: str
    description: str
    status: WorkflowStepStatus = WorkflowStepStatus.NOT_STARTED
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    error_message: Optional[str] = None
    output: Optional[Dict[str, Any]] = None


class BaseWorkflowState(TypedDict):
    """Base state interface that all workflow states should extend."""
    workflow_metadata: WorkflowMetadata
    error: Optional[str]
    debug_info: Dict[str, Any]


class WorkflowProgressCallback:
    """Callback interface for workflow progress updates."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    def on_workflow_start(self, metadata: WorkflowMetadata):
        """Called when workflow starts."""
        if self.verbose:
            print(f"Starting {metadata.workflow_type} workflow: {metadata.workflow_id}")

    def on_workflow_complete(self, metadata: WorkflowMetadata):
        """Called when workflow completes successfully."""
        if self.verbose:
            duration = metadata.duration_seconds or 0
            print(f"Workflow completed in {duration:.2f}s: {metadata.workflow_id}")

    def on_workflow_error(self, metadata: WorkflowMetadata, error: str):
        """Called when workflow encounters an error."""
        if self.verbose:
            print(f"Workflow failed: {metadata.workflow_id} - {error}")

    def on_step_start(self, step: WorkflowStep):
        """Called when a workflow step starts."""
        if self.verbose:
            print(f"  {step.name}: {step.description}")

    def on_step_complete(self, step: WorkflowStep):
        """Called when a workflow step completes."""
        if self.verbose:
            duration = step.duration_seconds or 0
            print(f"  {step.name} completed in {duration:.2f}s")

    def on_step_error(self, step: WorkflowStep, error: str):
        """Called when a workflow step encounters an error."""
        if self.verbose:
            print(f"  {step.name} failed: {error}")


class BaseWorkflow(ABC):
    """Abstract base class for all workflows."""

    def __init__(self, workflow_type: str, callback: Optional[WorkflowProgressCallback] = None):
        self.workflow_type = workflow_type
        self.callback = callback or WorkflowProgressCallback()
        self._steps: List[WorkflowStep] = []

    def _generate_workflow_id(self) -> str:
        """Generate a unique workflow ID."""
        timestamp = int(time.time() * 1000)
        return f"{self.workflow_type}_{timestamp}"

    def _create_metadata(self, **kwargs) -> WorkflowMetadata:
        """Create workflow metadata."""
        return WorkflowMetadata(
            workflow_id=self._generate_workflow_id(),
            workflow_type=self.workflow_type,
            status=WorkflowStatus.PENDING,
            total_steps=len(self._steps),
            tags=kwargs
        )

    def _start_workflow(self, metadata: WorkflowMetadata) -> WorkflowMetadata:
        """Mark workflow as started."""
        metadata.status = WorkflowStatus.RUNNING
        metadata.started_at = datetime.now(timezone.utc)
        self.callback.on_workflow_start(metadata)
        return metadata

    def _complete_workflow(self, metadata: WorkflowMetadata) -> WorkflowMetadata:
        """Mark workflow as completed."""
        metadata.status = WorkflowStatus.COMPLETED
        metadata.completed_at = datetime.now(timezone.utc)
        if metadata.started_at:
            metadata.duration_seconds = (metadata.completed_at - metadata.started_at).total_seconds()
        self.callback.on_workflow_complete(metadata)
        return metadata

    def _fail_workflow(self, metadata: WorkflowMetadata, error: str) -> WorkflowMetadata:
        """Mark workflow as failed."""
        metadata.status = WorkflowStatus.FAILED
        metadata.completed_at = datetime.now(timezone.utc)
        metadata.error_message = error
        if metadata.started_at:
            metadata.duration_seconds = (metadata.completed_at - metadata.started_at).total_seconds()
        self.callback.on_workflow_error(metadata, error)
        return metadata

    def _start_step(self, step_name: str) -> WorkflowStep:
        """Start a workflow step."""
        step = next((s for s in self._steps if s.name == step_name), None)
        if not step:
            step = WorkflowStep(name=step_name, description=f"Executing {step_name}")
            self._steps.append(step)

        step.status = WorkflowStepStatus.IN_PROGRESS
        step.started_at = datetime.now(timezone.utc)
        self.callback.on_step_start(step)
        return step

    def _complete_step(self, step: WorkflowStep, output: Optional[Dict[str, Any]] = None) -> WorkflowStep:
        """Complete a workflow step."""
        step.status = WorkflowStepStatus.COMPLETED
        step.completed_at = datetime.now(timezone.utc)
        step.output = output
        if step.started_at:
            step.duration_seconds = (step.completed_at - step.started_at).total_seconds()
        self.callback.on_step_complete(step)
        return step

    def _fail_step(self, step: WorkflowStep, error: str) -> WorkflowStep:
        """Fail a workflow step."""
        step.status = WorkflowStepStatus.FAILED
        step.completed_at = datetime.now(timezone.utc)
        step.error_message = error
        if step.started_at:
            step.duration_seconds = (step.completed_at - step.started_at).total_seconds()
        self.callback.on_step_error(step, error)
        return step

    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the workflow. Must be implemented by subclasses."""
        pass

    def get_step_summary(self) -> Dict[str, Any]:
        """Get a summary of all workflow steps."""
        return {
            "total_steps": len(self._steps),
            "completed_steps": len([s for s in self._steps if s.status == WorkflowStepStatus.COMPLETED]),
            "failed_steps": len([s for s in self._steps if s.status == WorkflowStepStatus.FAILED]),
            "steps": [
                {
                    "name": step.name,
                    "status": step.status.value,
                    "duration": step.duration_seconds,
                    "error": step.error_message
                }
                for step in self._steps
            ]
        }


class WorkflowExecutor:
    """Utility class for executing workflows with enhanced features."""

    @staticmethod
    async def execute_with_timeout(workflow: BaseWorkflow,
                                 timeout_seconds: float,
                                 **kwargs) -> Dict[str, Any]:
        """Execute a workflow with a timeout."""
        try:
            return await asyncio.wait_for(
                workflow.execute(**kwargs),
                timeout=timeout_seconds
            )
        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": f"Workflow timed out after {timeout_seconds} seconds",
                "timeout": True
            }

    @staticmethod
    async def execute_with_retry(workflow: BaseWorkflow,
                               max_retries: int = 3,
                               retry_delay: float = 1.0,
                               **kwargs) -> Dict[str, Any]:
        """Execute a workflow with retry logic."""
        last_error = None

        for attempt in range(max_retries + 1):
            try:
                result = await workflow.execute(**kwargs)
                if result.get("success", False):
                    if attempt > 0:
                        result["retry_attempt"] = attempt
                    return result
                else:
                    last_error = result.get("error", "Unknown error")
            except Exception as e:
                last_error = str(e)

            if attempt < max_retries:
                await asyncio.sleep(retry_delay * (2 ** attempt))  # Exponential backoff

        return {
            "success": False,
            "error": f"Workflow failed after {max_retries + 1} attempts. Last error: {last_error}",
            "retries_exhausted": True,
            "attempts": max_retries + 1
        }

    @staticmethod
    async def execute_parallel_workflows(workflows: List[BaseWorkflow],
                                       **kwargs) -> List[Dict[str, Any]]:
        """Execute multiple workflows in parallel."""
        tasks = [workflow.execute(**kwargs) for workflow in workflows]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "success": False,
                    "error": str(result),
                    "workflow_index": i,
                    "exception": True
                })
            else:
                # result is Dict[str, Any] here
                workflow_result = cast(Dict[str, Any], result)
                workflow_result["workflow_index"] = i
                processed_results.append(workflow_result)

        return processed_results


class WorkflowConfig:
    """Configuration management for workflows."""

    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        self.config = config_dict or {}

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value

    def load_from_file(self, file_path: str) -> None:
        """Load configuration from a JSON file."""
        try:
            with open(file_path, 'r') as f:
                self.config.update(json.load(f))
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise ValueError(f"Failed to load config from {file_path}: {e}")

    def save_to_file(self, file_path: str) -> None:
        """Save configuration to a JSON file."""
        try:
            with open(file_path, 'w') as f:
                json.dump(self.config, f, indent=2, default=str)
        except Exception as e:
            raise ValueError(f"Failed to save config to {file_path}: {e}")


# Utility functions
def create_workflow_callback(verbose: bool = False) -> WorkflowProgressCallback:
    """Create a workflow progress callback."""
    return WorkflowProgressCallback(verbose=verbose)


def merge_workflow_results(*results: Dict[str, Any]) -> Dict[str, Any]:
    """Merge multiple workflow results into a single result."""
    merged = {
        "success": all(r.get("success", False) for r in results),
        "results": list(results),
        "total_workflows": len(results),
        "successful_workflows": len([r for r in results if r.get("success", False)]),
        "failed_workflows": len([r for r in results if not r.get("success", False)]),
        "errors": [r.get("error") for r in results if r.get("error")]
    }

    # Merge metadata if present
    all_metadata = [r.get("metadata", {}) for r in results if r.get("metadata")]
    if all_metadata:
        merged["metadata"] = {
            "combined_metadata": all_metadata,
            "total_duration": sum(m.get("duration_seconds", 0) for m in all_metadata),
            "average_duration": sum(m.get("duration_seconds", 0) for m in all_metadata) / len(all_metadata)
        }

    return merged