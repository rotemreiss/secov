from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="secov",
    version="0.9",
    author="Rotem Reiss",
    author_email="reiss.r@gmail.com",
    description="Determine the security coverage from code project.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/rotemreiss/secov",
    packages=find_packages(exclude=['tests*']),
    install_requires=['GitPython'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        'console_scripts': [
            'secov=secov.main:interactive',
        ],
    },
)