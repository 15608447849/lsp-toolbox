import setuptools

# setup说明 https://packaging.python.org/en/latest/tutorials/packaging-projects/

# python -m build
# python  -m twine upload --repository pypi dist/*

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name = "lsptoolbox",
    version = "0.0.5",
    author = "lee bottle",
    author_email = "793065165@qq.com",
    description="my python project tool box.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/15608447849/lsp-toolbox",
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
