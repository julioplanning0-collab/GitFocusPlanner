"""
V3 PURE - NO V2 LOGIC ALLOWED

Flask server for V3 timeline-linear architecture.

CRITICAL RULES:
- Run on port 5001 (to avoid conflict with V2 server on 5000)
- NO imports from backend/planning_engine/ (old V2 code)
- Serves ONLY V3 API endpoints + static files
- NO server-side rendering for planning (client-side only)

Usage:
    python -m webapp_v3_pure.server_v3
    OR
    python webapp_v3_pure/server_v3.py
"""

import sys
import logging
from pathlib import Path
from flask import Flask, render_template
from flask_cors import CORS

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from webapp_v3_pure.api.routes_v3 import bp as api_v3_bp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app():
    """Create and configure Flask application"""
    app = Flask(
        __name__,
        template_folder='templates',
        static_folder='static'
    )

    # Enable CORS for API endpoints
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Configuration
    app.config['JSON_SORT_KEYS'] = False
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

    # Register blueprints
    app.register_blueprint(api_v3_bp)

    # Root route
    @app.route('/')
    def index():
        """Redirect to V3 interface"""
        return render_template('gitfocus_v3.html')

    @app.route('/gitfocus-v3')
    def gitfocus_v3():
        """V3 interface page"""
        return render_template('gitfocus_v3.html')

    # Health check
    @app.route('/health')
    def health():
        """Server health check"""
        return {
            'success': True,
            'service': 'GitFocus V3 Pure Server',
            'version': '3.0.0'
        }

    logger.info("V3 Pure Flask app created")
    return app


def main():
    """Run development server"""
    app = create_app()

    logger.info("="*60)
    logger.info("GitFocus Planner V3 Pure - Starting Server")
    logger.info("="*60)
    logger.info("Architecture: Timeline Linear (V3 Pure)")
    logger.info("Port: 5001")
    logger.info("Interface: http://localhost:5001/gitfocus-v3")
    logger.info("API: http://localhost:5001/api/v3/health")
    logger.info("="*60)

    app.run(
        host='0.0.0.0',
        port=5001,
        debug=True,
        use_reloader=True
    )


if __name__ == '__main__':
    main()
