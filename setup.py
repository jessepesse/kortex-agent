"""
Kortex Agent Setup Configuration
"""

from setuptools import setup, find_packages

setup(
    name="kortex",
    version="1.0.0-alpha6",
    description="Kortex Agent - Personal AI Assistant with Council LLM",
    author="Jesse Saarinen",
    packages=find_packages(),
    install_requires=[
        "google-generativeai>=0.3.2",
        "openai>=1.6.1",
        "python-dotenv>=1.0.0",
        "flask>=3.0.0",
        "flask-cors>=4.0.0",
    ],
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            # CLI removed per user request - web only
        ],
    },
)
