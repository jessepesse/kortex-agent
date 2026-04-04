"""
Kortex Agent Setup Configuration
"""

from setuptools import setup, find_packages

setup(
    name="kortex",
    version="1.0.0",
    description="Kortex Agent - Personal AI Assistant with Council LLM",
    author="Jesse Saarinen",
    packages=find_packages(),
    install_requires=[
        "google-genai>=1.0.0",
        "openai>=2.21.0",
        "python-dotenv>=1.2.1",
        "flask>=3.1.3",
        "flask-cors>=6.0.2",
    ],
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            # CLI removed per user request - web only
        ],
    },
)
