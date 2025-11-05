"""
Flask Server - GitFocus Planner V2

Main application entry point.
Configures Flask app, registers blueprints, sets up logging.
"""

import logging
import sys
from flask import Flask
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from webapp.config import Config


def create_app():
    """
    Create and configure Flask application.

    Returns:
        Configured Flask app
    """
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(Config)

    # Setup logging
    setup_logging(app.config['LOG_LEVEL'])

    # Validate configuration
    try:
        Config.validate()
        logging.info(f"Configuration validated: {Config.info()}")
    except RuntimeError as e:
        logging.error(f"Configuration invalid: {e}")
        raise

    # Register blueprints
    from webapp.api.routes_gitfocus_v2 import gitfocus_bp
    app.register_blueprint(gitfocus_bp)

    # Health check endpoint
    @app.route('/health')
    def health_check():
        """Health check endpoint."""
        return {
            'status': 'healthy',
            'version': '2.0',
            'config': Config.info()
        }

    # Root redirect
    @app.route('/')
    def index():
        """Redirect to main interface."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>GitFocus Planner V2</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
                    max-width: 600px;
                    margin: 100px auto;
                    padding: 20px;
                    text-align: center;
                }
                h1 { color: #3b82f6; }
                a {
                    display: inline-block;
                    margin: 10px;
                    padding: 12px 24px;
                    background: #3b82f6;
                    color: white;
                    text-decoration: none;
                    border-radius: 6px;
                }
                a:hover { background: #2563eb; }
                .version { color: #6b7280; margin-top: 40px; }
            </style>
        </head>
        <body>
            <h1>🎯 GitFocus Planner V2</h1>
            <p>Intelligent Pomodoro Planning with Learning System</p>
            <div>
                <a href="/api/v2/gitfocus/interface">📋 Planning Interface</a>
                <a href="/health">❤️ Health Check</a>
            </div>
            <div class="version">Version 2.0 - Apprentissage Intelligent</div>
        </body>
        </html>
        """

    logging.info(f"Flask app created successfully")
    return app


def setup_logging(log_level: str):
    """
    Configure application logging.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    # Convert string to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Configure root logger
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Set levels for specific loggers
    logging.getLogger('werkzeug').setLevel(logging.WARNING)  # Flask request logs


def main():
    """
    Main entry point for running the server directly.
    """
    app = create_app()

    print("=" * 60)
    print(" GitFocus Planner V2 - Starting Server")
    print("=" * 60)
    print(f" Host: {Config.HOST}")
    print(f" Port: {Config.PORT}")
    print(f" Debug: {Config.DEBUG}")
    print(f" Data: {Config.DATA_DIR}")
    print("=" * 60)
    print(f" Web Interface: http://localhost:{Config.PORT}/api/v2/gitfocus/interface")
    print(f" Health Check: http://localhost:{Config.PORT}/health")
    print("=" * 60)

    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )


if __name__ == '__main__':
    main()
