#!/usr/bin/env python3
"""Setup configuration for Grace CLI - Global Command Executor."""

from setuptools import setup, find_packages
from pathlib import Path

here = Path(__file__).parent.absolute()
readme = here / "README.md"
long_description = readme.read_text(encoding="utf-8") if readme.exists() else ""

setup(
    name="grace-cli",
    version="1.0.0",
    description="GRACE CLI - Global command executor for all grace modules",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="juspay/grace",
    author_email="manideepk90@gmail.com",
    url="https://github.com/juspay/grace",
    packages=find_packages(exclude=['tests', 'modules']),
    package_dir={'': 'scripts'},
    py_modules=['grace_cli', 'grace_registry'],
    python_requires=">=3.8",
    install_requires=[
        "click>=8.0.0",
        "rich>=13.0.0",
    ],
    entry_points={
        "console_scripts": [
            "grace=grace_cli:main",
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
    keywords="cli automation tools grace",
    include_package_data=True,
    zip_safe=False,
)
