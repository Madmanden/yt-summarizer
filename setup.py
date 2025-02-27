from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="yt-summarizer",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A tool to summarize YouTube videos using AI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/yt-summarizer",
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        "youtube-transcript-api>=0.6.1",
        "requests>=2.31.0",
        "python-dotenv>=1.0.0",
        "argparse>=1.4.0",
        "rich>=13.5.0",
    ],
    entry_points={
        "console_scripts": [
            "yt-summarize=yt_summarizer.cli:main",
        ],
    },
    package_data={
        "yt_summarizer": ["../.env.example"],
    },
)