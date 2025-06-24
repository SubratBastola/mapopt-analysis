"""
Setup script for MAPopt Analysis Tool
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="mapopt-analysis",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A biomedical signal analysis tool for calculating optimal MAP and burden metrics",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/mapopt-analysis",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "mapopt-analysis=mapopt_analysis.main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
) 
