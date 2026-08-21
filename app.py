import os
from flask import Flask, render_template, session, redirect, url_for, send_from_directory
from config import Config
from database.db import close_db, query_db

def create_app():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    template_candidates = [
        os.path.join(base_dir, 'templates'),
        os.path.join(os.path.dirname(base_dir), 'templates'),
        os.path.join(os.getcwd(), 'templates'),
        '/var/task/templates'
    ]
    template_dir = next((p for p in template_candidates if os.path.exists(p)), os.path.join(base_dir, 'templates'))
    
    static_candidates = [
        os.path.join(base_dir, 'static'),
        os.path.join(os.path.dirname(base_dir), 'static'),
        os.path.join(os.getcwd(), 'static'),
        '/var/task/static'
    ]
    static_dir = next((p for p in static_candidates if os.path.exists(p)), os.path.join(base_dir, 'static'))

    app = Flask(
        __name__,
        template_folder=template_dir,
        static_folder=static_dir,
        static_url_path='/static'
    )
    app.url_map.strict_slashes = False
    app.config.from_object(Config)

    @app.route('/static/<path:filename>')
    def serve_custom_static(filename):
        for s_dir in static_candidates:
            if s_dir and os.path.exists(os.path.join(s_dir, filename)):
                return send_from_directory(s_dir, filename)
        if app.static_folder and os.path.exists(os.path.join(app.static_folder, filename)):
            return send_from_directory(app.static_folder, filename)
        return "Asset not found", 404

    @app.route('/debug-env')
    def debug_env():
        from flask import request
        return {k: str(v) for k, v in request.environ.items() if not k.startswith('wsgi.')}



    # Register DB teardown
    app.teardown_appcontext(close_db)

    # Register Blueprints
    from routes.auth import auth_bp
    from routes.user import user_bp
    from routes.booking import booking_bp
    from routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(booking_bp)
    app.register_blueprint(admin_bp)

    # Public Landing Page
    @app.route('/')
    @app.route('/api/index')
    @app.route('/api')
    def index():
        # Live overview stats for landing page hero
        stats = {
            'total_slots': 0,
            'available_slots': 0,
            'total_bookings': 0
        }
        try:
            total_slots = query_db("SELECT COUNT(*) as c FROM parking_slots", one=True)
            available_slots = query_db("SELECT COUNT(*) as c FROM parking_slots WHERE status = 'available'", one=True)
            total_bookings = query_db("SELECT COUNT(*) as c FROM bookings", one=True)
            if total_slots:
                stats['total_slots'] = total_slots['c']
            if available_slots:
                stats['available_slots'] = available_slots['c']
            if total_bookings:
                stats['total_bookings'] = total_bookings['c']
        except Exception:
            pass

        return render_template('index.html', stats=stats)

    # PBL-II / Future Scope Page
    @app.route('/future-scope')
    def future_scope():
        return render_template('future_scope.html')

    # Error Handlers
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(e):
        try:
            return render_template('errors/500.html'), 500
        except Exception:
            return "<h1>500 Internal Server Error</h1>", 500

    @app.errorhandler(Exception)
    def unhandled_exception(e):
        try:
            return render_template('errors/500.html'), 500
        except Exception:
            return f"<h1>Application Error</h1><p>{str(e)}</p>", 500

    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = Config.DEBUG
    print(f"Starting SmartPark on http://127.0.0.1:{port} (Debug: {debug})")
    app.run(host='0.0.0.0', port=port, debug=debug)
