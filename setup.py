import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="PyPAKParser",
    version="1.0.1",
    author="Ricky Davis",
    author_email="ricky.c.davis.9@gmail.com",
    description="Unreal Engine PAK Parser written in Python 3 originally for the game Astroneer",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/AstroTechies/PyPAKParser",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3.7",
        'Intended Audience :: Developers',
        'Natural Language :: English',
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
