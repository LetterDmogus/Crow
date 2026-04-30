#!/usr/bin/env python3
"""
setup.py — Install crow as a global CLI command
"""
from setuptools import setup, find_packages

setup(
    name="crow",
    version="1.1.0",
    description="FTP harness for AI assistants (Claude Code, Gemini CLI, etc.)",
    packages=find_packages(),
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "crow=crow.cli:main",
        ],
    },
)
