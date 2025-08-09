#!/usr/bin/env python3
"""Setup script for Proxmox MCP Server."""

from setuptools import setup, find_packages

# Read the README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="proxmox-mcp",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Model Context Protocol server for Proxmox VE management",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/proxmox-mcp",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: System :: Systems Administration",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
        ],
        "docker": [
            "docker>=6.1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "proxmox-mcp=src.cli:cli",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
