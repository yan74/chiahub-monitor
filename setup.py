from distutils.core import setup
import setuptools


dependencies=[
    "setuptools~=57.0.0",
    "aiohttp~=3.7.4",
    "PyYAML~=5.4.1",
]

setup(
    name="chiahub_monitor",
    version="0.0.5",
    author="Yan Hackl-Feldbusch",
    author_email="yan@cryptico.io",
    description="A monitoring utility for chia blockchain",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yan74/chiahub-monitor",
    install_requires=dependencies,
    packages=setuptools.find_packages(),
    project_urls={
        "Bug Tracker": "https://github.com/yan74/chiahub-monitor/issues"
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
