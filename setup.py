from setuptools import setup, find_packages

with open("requirements.txt", "r") as f:
    dependencies = f.read().splitlines()

setup(
    name="p2pchat",
    version="0.0",
    description="A modular peer-to-peer chat system in Python",
    author="Ziad Amerr",
    author_email="ziad.amerr@yahoo.com",
    packages=find_packages(),
    install_requires=dependencies,  # from requirements.txt
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)
