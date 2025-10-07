#!/usr/bin/env python3
"""Setup configuration for Deep Research CLI."""

from setuptools import setup
from pathlib import Path

# Get the directory containing setup.py
here = Path(__file__).parent.absolute()

# Read the README file
readme_file = here / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements
requirements_file = here / "requirements.txt"
if requirements_file.exists():
    with open(requirements_file) as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]
else:
    requirements = []

setup(
    name="grace-research-cli",
    version="1.0.0",
    description="GRACE Deep Research CLI - Intelligent web research with AI analysis",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="juspay/grace",
    author_email="manideepk90@gmail.com",
    url="https://github.com/juspay/grace",
    packages=['research_types', 'services', 'utils'],
    py_modules=['run_cli', 'cli', '__init__', '__main__'],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "grace-research=run_cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    keywords="research cli ai web-scraping analysis",
    include_package_data=True,
    zip_safe=False,
)
