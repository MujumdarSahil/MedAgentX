"""
Setup script for MedAgentX platform.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text() if readme_file.exists() else ""

setup(
    name="medagentx",
    version="0.1.0",
    description="MedAgentX - E-Doctor OS: Programmable Agentic AI Platform for Clinical Decision Support",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="MedAgentX Team",
    author_email="contact@medagentx.com",
    url="https://github.com/medagentx/platform",
    packages=find_packages(exclude=["tests", "tests.*"]),
    python_requires=">=3.10",
    install_requires=[
        # Core dependencies are in requirements.txt
        # This is a placeholder - in production, list dependencies here
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
            "mypy>=1.6.0",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Healthcare Industry",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
    ],
)

