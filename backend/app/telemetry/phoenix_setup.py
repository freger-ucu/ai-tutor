"""
Phoenix Telemetry Setup

Configures OpenTelemetry tracing with Phoenix for LLM observability.
Enable via PHOENIX_ENABLED=true in .env
"""

# Ensure GRPC env vars are set before any grpcio imports
import os
os.environ.setdefault("GRPC_ENABLE_FORK_SUPPORT", "0")
os.environ.setdefault("OBJC_DISABLE_INITIALIZE_FORK_SAFETY", "YES")
os.environ.setdefault("GRPC_POLL_STRATEGY", "poll")
os.environ.setdefault("GRPC_VERBOSITY", "ERROR")

import logging
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)

_tracer_provider: Optional[object] = None
_initialized: bool = False


def setup_phoenix() -> bool:
    """
    Initialize Phoenix telemetry if enabled.

    Returns:
        True if Phoenix was successfully initialized, False otherwise.
    """
    global _tracer_provider, _initialized

    if _initialized:
        return _tracer_provider is not None

    _initialized = True

    if not settings.phoenix_enabled:
        logger.info("Phoenix telemetry disabled (PHOENIX_ENABLED=false)")
        return False

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from openinference.instrumentation.openai import OpenAIInstrumentor

        # Create resource with service name
        resource = Resource.create({
            "service.name": "ai-tutor-backend",
            "service.version": settings.app_version,
        })

        # Create tracer provider
        _tracer_provider = TracerProvider(resource=resource)

        # Configure exporter
        if settings.phoenix_endpoint:
            endpoint = settings.phoenix_endpoint
            if not endpoint.endswith("/v1/traces"):
                endpoint = f"{endpoint.rstrip('/')}/v1/traces"

            exporter = OTLPSpanExporter(endpoint=endpoint)
            _tracer_provider.add_span_processor(BatchSpanProcessor(exporter))
            logger.info(f"Phoenix exporter configured: {endpoint}")
        else:
            # Local Phoenix - use default endpoint
            try:
                import phoenix as px
                # Start local Phoenix if no endpoint specified
                px.launch_app()
                exporter = OTLPSpanExporter(endpoint="http://localhost:6006/v1/traces")
                _tracer_provider.add_span_processor(BatchSpanProcessor(exporter))
                logger.info("Phoenix local UI started at http://localhost:6006")
            except Exception as e:
                logger.warning(f"Could not start local Phoenix: {e}")
                return False

        # Set as global tracer provider
        trace.set_tracer_provider(_tracer_provider)

        # Instrument OpenAI client
        OpenAIInstrumentor().instrument()
        logger.info("OpenAI instrumentation enabled")

        logger.info("Phoenix telemetry initialized successfully")
        return True

    except ImportError as e:
        logger.warning(f"Phoenix dependencies not installed: {e}")
        logger.warning("Install with: pip install arize-phoenix openinference-instrumentation-openai")
        return False
    except Exception as e:
        logger.error(f"Failed to initialize Phoenix: {e}")
        return False


def get_tracer(name: str = "ai-tutor"):
    """Get a tracer for manual span creation."""
    if _tracer_provider is None:
        return None

    from opentelemetry import trace
    return trace.get_tracer(name)


def shutdown_phoenix():
    """Shutdown Phoenix telemetry gracefully."""
    global _tracer_provider

    if _tracer_provider is not None:
        try:
            _tracer_provider.shutdown()
            logger.info("Phoenix telemetry shutdown complete")
        except Exception as e:
            logger.warning(f"Error during Phoenix shutdown: {e}")
        finally:
            _tracer_provider = None
