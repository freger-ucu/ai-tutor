"""
LangSmith Tracing Integration

Provides tracing for LLM calls and agentic workflows.
"""

# Ensure GRPC env vars are set before any grpcio imports
import os
os.environ.setdefault("GRPC_ENABLE_FORK_SUPPORT", "0")
os.environ.setdefault("OBJC_DISABLE_INITIALIZE_FORK_SAFETY", "YES")
os.environ.setdefault("GRPC_POLL_STRATEGY", "poll")
os.environ.setdefault("GRPC_VERBOSITY", "ERROR")

import logging
from typing import Optional, Any, Callable
from contextlib import contextmanager

from app.config import settings

logger = logging.getLogger(__name__)


def _setup_langsmith():
    """Configure LangSmith environment variables."""
    # DISABLED: LangSmith causes grpcio mutex.cc crash on macOS
    # To re-enable, set LANGSMITH_FORCE_ENABLE=true in environment
    if os.environ.get("LANGSMITH_FORCE_ENABLE", "").lower() == "true":
        if settings.langsmith_enabled and settings.langsmith_api_key:
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key
            os.environ["LANGCHAIN_PROJECT"] = settings.langsmith_project
            os.environ["LANGCHAIN_ENDPOINT"] = settings.langsmith_endpoint
            return True
    return False


# Initialize on module load
_langsmith_available = _setup_langsmith()

# Lazy import of langsmith to avoid grpcio initialization at module load (macOS mutex.cc issue)
_langsmith_imported = None
_traceable = None
_Client = None
_RunTree = None


def _lazy_import_langsmith():
    """Lazily import langsmith modules on first use."""
    global _langsmith_imported, _traceable, _Client, _RunTree
    if _langsmith_imported is not None:
        return _langsmith_imported
    try:
        from langsmith import traceable, Client
        from langsmith.run_trees import RunTree
        _traceable = traceable
        _Client = Client
        _RunTree = RunTree
        _langsmith_imported = True
    except ImportError:
        _langsmith_imported = False
    return _langsmith_imported


def is_tracing_enabled() -> bool:
    """Check if LangSmith tracing is available and enabled."""
    return _langsmith_available and _lazy_import_langsmith()


def trace(
    name: Optional[str] = None,
    run_type: str = "chain",
    metadata: Optional[dict] = None,
    tags: Optional[list[str]] = None
):
    """
    Decorator to trace a function with LangSmith.

    IMPORTANT: This decorator is truly lazy - it only imports langsmith when
    the decorated function is actually CALLED, not when it's decorated.
    This avoids grpcio initialization at module import time (macOS mutex.cc issue).

    Args:
        name: Name for the trace (defaults to function name)
        run_type: Type of run ("chain", "llm", "tool", "retriever")
        metadata: Additional metadata to attach
        tags: Tags for filtering in LangSmith UI

    Usage:
        @trace(name="generate_question", run_type="chain")
        async def generate_question(...):
            ...
    """
    import functools
    import asyncio

    def decorator(func: Callable) -> Callable:
        # Store the traced version lazily
        _traced_func = None

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            nonlocal _traced_func
            # Lazy initialization on first call
            if _traced_func is None:
                if is_tracing_enabled():
                    _traced_func = _traceable(
                        name=name or func.__name__,
                        run_type=run_type,
                        metadata=metadata or {},
                        tags=tags or []
                    )(func)
                else:
                    _traced_func = func
            return await _traced_func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            nonlocal _traced_func
            # Lazy initialization on first call
            if _traced_func is None:
                if is_tracing_enabled():
                    _traced_func = _traceable(
                        name=name or func.__name__,
                        run_type=run_type,
                        metadata=metadata or {},
                        tags=tags or []
                    )(func)
                else:
                    _traced_func = func
            return _traced_func(*args, **kwargs)

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def trace_llm(
    name: Optional[str] = None,
    metadata: Optional[dict] = None
):
    """Shorthand for tracing LLM calls."""
    return trace(name=name, run_type="llm", metadata=metadata)


def trace_chain(
    name: Optional[str] = None,
    metadata: Optional[dict] = None,
    tags: Optional[list[str]] = None
):
    """Shorthand for tracing chain/workflow steps."""
    return trace(name=name, run_type="chain", metadata=metadata, tags=tags)


def trace_tool(
    name: Optional[str] = None,
    metadata: Optional[dict] = None
):
    """Shorthand for tracing tool calls."""
    return trace(name=name, run_type="tool", metadata=metadata)


def trace_retriever(
    name: Optional[str] = None,
    metadata: Optional[dict] = None
):
    """Shorthand for tracing retrieval operations."""
    return trace(name=name, run_type="retriever", metadata=metadata)


@contextmanager
def trace_context(
    name: str,
    run_type: str = "chain",
    inputs: Optional[dict] = None,
    metadata: Optional[dict] = None,
    tags: Optional[list[str]] = None
):
    """
    Context manager for tracing a block of code.

    Usage:
        with trace_context("process_batch", inputs={"batch_size": 5}):
            # do work
            pass
    """
    if not is_tracing_enabled():
        yield None
        return

    run_tree = _RunTree(
        name=name,
        run_type=run_type,
        inputs=inputs or {},
        extra={"metadata": metadata or {}},
        tags=tags or []
    )

    try:
        yield run_tree
    except Exception as e:
        run_tree.end(error=str(e))
        run_tree.post()
        raise
    else:
        run_tree.end()
        run_tree.post()


def log_feedback(
    run_id: str,
    key: str,
    score: float,
    comment: Optional[str] = None
):
    """
    Log feedback for a run (e.g., validation results).

    Args:
        run_id: The run ID to attach feedback to
        key: Feedback key (e.g., "correctness", "relevance")
        score: Score value (0-1)
        comment: Optional comment
    """
    if not is_tracing_enabled():
        return

    try:
        client = _Client()
        client.create_feedback(
            run_id=run_id,
            key=key,
            score=score,
            comment=comment
        )
    except Exception as e:
        logger.warning(f"Failed to log feedback: {e}")


def get_tracing_url(run_id: str) -> Optional[str]:
    """Get the LangSmith URL for a specific run."""
    if not is_tracing_enabled():
        return None

    return f"{settings.langsmith_endpoint}/o/default/projects/p/{settings.langsmith_project}/r/{run_id}"
