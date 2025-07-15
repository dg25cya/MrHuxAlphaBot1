from setuptools import setup, find_packages

setup(
    name="sma-telebot",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.10",
    install_requires=[
        "telethon>=1.28.0",
        "fastapi>=0.104.0",
        "sqlalchemy>=2.0.0",
        "alembic>=1.11.0",
        "pydantic>=2.3.0",
        "pydantic-settings>=2.1.0",
        "httpx>=0.24.0",
        "redis>=4.5.0",
        "loguru>=0.7.0",
        "prometheus-client>=0.17.0",
        "python-telegram-bot>=20.3",
        "psycopg2-binary>=2.9.9",
        "beautifulsoup4>=4.12.0",
        "uvicorn>=0.21.0",
        "python-dotenv>=1.1.0",
        "tzdata>=2025.2",
        "base58>=2.1.1",
    ],
)
