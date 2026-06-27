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
    version="2.0.0",
    description="MedAgentX: A Governance-First Deterministic Multi-Agent Clinical Intelligence Platform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Sahil Mujumdar",
    author_email="mujumdarsahil05@gmail.com",
    url="https://github.com/MujumdarSahil/MedAgentX",
    packages=find_packages(exclude=["tests", "tests.*", "evaluation", "evaluation.*"]),
    python_requires=">=3.10",
    install_requires=[
        # Runtime dependencies listed in requirements.txt
        # For packaging purposes, pin core deps here if publishing to PyPI
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
            "mypy>=1.6.0",
        ],
        "eval": [
            "scipy>=1.11.0",
            "statsmodels>=0.14.0",
            "matplotlib>=3.7.0",
            "seaborn>=0.12.0",
            "tiktoken>=0.5.0",
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
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
    ],
)

