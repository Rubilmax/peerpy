import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="peerpy",
    version="0.9.0",
    author="Rubilmax",
    author_email="rmilon@gmail.com",
    description="p2p connection over TCP made dead simple!",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Rubilmax/peerpy",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
