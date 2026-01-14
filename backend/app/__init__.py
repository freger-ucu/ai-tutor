"""
AI Tutor Backend Application

FastAPI-based backend for the AI Tutor system.
"""

# IMPORTANT: Set environment variables BEFORE any imports
# This fixes the mutex.cc issue on macOS caused by grpcio fork safety
import os

os.environ.setdefault("GRPC_ENABLE_FORK_SUPPORT", "0")
os.environ.setdefault("OBJC_DISABLE_INITIALIZE_FORK_SAFETY", "YES")
os.environ.setdefault("GRPC_POLL_STRATEGY", "poll")
# Prevent grpc from using fork-unsafe operations
os.environ.setdefault("GRPC_VERBOSITY", "ERROR")
