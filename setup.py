import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="python-p2p",
    version="0.1.0",
    author="Rubilmax",
    author_email="rmilon@gmail.com",
    description="p2p connection over TCP made dead simple!",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Rubilmax/python-p2p",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
