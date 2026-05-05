"""Bingody CLI 入口点配置"""

from setuptools import setup, find_packages

setup(
    name="bingdio",
    version="0.1.0",
    description="Bingody - CLI 个人 AI 音乐智能体",
    packages=find_packages(),
    package_data={
        "bingdio": ["py.typed"],
    },
    include_package_data=True,
    install_requires=[
        "textual>=0.80.0",
        "SQLAlchemy>=2.0",
        "PyYAML>=6.0",
        "requests>=2.31.0",
        "pycryptodome>=3.20.0",
    ],
    entry_points={
        "console_scripts": [
            "bingody=bingdio.main:run",
        ],
    },
    python_requires=">=3.10",
)
