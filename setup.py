from setuptools import setup, find_packages

setup(
    name="agent-kill-switch",
    version="1.0.0",
    description="The Out-of-Band Dead-Man's Switch & Multi-Party Emergency Breaker for Autonomous AI Agents",
    author="Ahmed Hassan",
    author_email="ahmed.alaa.hassan25@gmail.com",
    packages=find_packages(),
    python_requires=">=3.8",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
