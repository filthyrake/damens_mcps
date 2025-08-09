#!/usr/bin/env python3
"""
Setup script for pfSense MCP Server.
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="pfsense-mcp",
    version="1.0.0",
    author="pfSense MCP Team",
    author_email="support@example.com",
    description="A comprehensive MCP server for pfSense firewall management",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/pfsense-mcp",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: System :: Networking :: Firewalls",
        "Topic :: System :: Systems Administration",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "pfsense-mcp=src.http_pfsense_server:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="pfsense firewall mcp model-context-protocol networking",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/pfsense-mcp/issues",
        "Source": "https://github.com/yourusername/pfsense-mcp",
        "Documentation": "https://github.com/yourusername/pfsense-mcp#readme",
    },
)
