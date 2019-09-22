import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="abstruct",
    version="0.0.1",
    author="Gianluca Pacchiella",
    author_email="gp@ktln2.org",
    description="File formats for humans",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/gipi/abstruct",
    packages=setuptools.find_packages(),
    install_requires=[
        'capstone',
        'bitstring',
        'pillow',
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GPLv2 License",
        "Operating System :: OS Independent",
    ],
)
