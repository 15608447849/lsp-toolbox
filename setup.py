import setuptools

# setup说明
# https://packaging.python.org/en/latest/tutorials/packaging-projects/

setuptools.setup(
    name = "lsptoolbox",
    version = "0.0.1",
    author = "lee bottle",
    author_email = "793065165@qq.com",
    description="my python project tool box.",
    package_dir={"": "modules"},
    packages=setuptools.find_packages(where="modules"),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6"
)
