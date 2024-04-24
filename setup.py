import setuptools

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

with open("requirements.txt", "r", encoding="utf-8") as f:
    requires = f.read()

with open("github.txt", "r", encoding="utf-8") as f:
    cfg = f.read().split("|")

setuptools.setup(
    name="better-qq-botpy",
    version=cfg[0],
    license="MIT",
    author="Drelf2018",
    author_email="drelf2018@outlook.com",
    description="更好的 QQ 频道机器人",
    long_description_content_type="text/markdown",
    long_description=long_description,
    packages=setuptools.find_packages(),
    install_requires=requires.splitlines(),
    keywords=['python', 'qq', 'guildbbot'],
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Operating System :: Unix",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
    ],
    url="https://github.com/Drelf2018/GuildBot",
    python_requires=">=3.8",
)