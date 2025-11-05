"""
Configuration Module - GitFocus Planner V2

Environment variables:
- DATA_DIR: Path to prod_data/ directory
- HOST: Server host (default 0.0.0.0)
- PORT: Server port (default 5000)
- DEBUG: Debug mode (default True for development)
- LOG_LEVEL: Logging level (default INFO)
"""

import os
from pathlib import Path


class Config:
    """Application configuration."""

    # Data directory (production CSV files)
    DATA_DIR = Path(os.getenv(
        'DATA_DIR',
        r'C:\Users\juli0\AndroidStudioProjects\GitfocusPlanner\prod_data'
    ))

    # Server settings
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 'yes')

    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    JSON_SORT_KEYS = False  # Preserve dict order in JSON responses

    @classmethod
    def validate(cls):
        """
        Validate configuration.

        Raises:
            RuntimeError: If configuration invalid
        """
        if not cls.DATA_DIR.exists():
            raise RuntimeError(f"DATA_DIR does not exist: {cls.DATA_DIR}")

        required_files = [
            'LISTE_MERE.v2.csv',
            'TACHES_RECURRENTES.v2.csv',
            'TACHES_PLANIFIEES.v2.csv',
            'temps_morts.csv',
            'categories.csv'
        ]

        missing = []
        for filename in required_files:
            if not (cls.DATA_DIR / filename).exists():
                missing.append(filename)

        if missing:
            raise RuntimeError(f"Missing required CSV files in {cls.DATA_DIR}: {missing}")

    @classmethod
    def info(cls) -> dict:
        """
        Get configuration info.

        Returns:
            Configuration dictionary
        """
        return {
            'data_dir': str(cls.DATA_DIR),
            'host': cls.HOST,
            'port': cls.PORT,
            'debug': cls.DEBUG,
            'log_level': cls.LOG_LEVEL
        }
