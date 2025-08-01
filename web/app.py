from flask import Flask
from ids.web.extensions import db
from ids.web.routes import register_blueprints


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY="devkey",
        SQLALCHEMY_DATABASE_URI="postgresql://postgres:postgres321@localhost/net_analysis",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    db.init_app(app)
    register_blueprints(app)
    @app.route("/")                   # <-- new root route
    def _root():
        return redirect(url_for("auth.login"))
    # ---------- safe place: we ARE inside app.app_context ----------
    with app.app_context():
        db.create_all()

        # ensure default admin
        from ids.web.routes.auth import User  # local import to avoid cycles
        if not User.query.filter_by(username="admin").first():
            admin = User(username="admin", role="admin")
            admin.set_password("changeme")
            db.session.add(admin)
            db.session.commit()
            print("🛈 Created default admin (admin / changeme)")

    return app


if __name__ == "__main__":           # allow: python -m ids.web.app
    create_app().run(debug=True)



#"postgresql://postgres:postgres321@localhost/net_analysis",