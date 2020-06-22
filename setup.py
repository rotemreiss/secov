import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="secov",
    version="0.0.1",
    author="Rotem Reiss",
    author_email="reiss.r@gmail.com",
    description="Determine the security coverage from code project.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/rotemreiss/secov",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ]
)