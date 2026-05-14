from flask import (Flask, render_template, request, jsonify,
                   send_file, redirect, url_for)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (LoginManager, UserMixin, login_user,
                         logout_user, login_required, current_user)
from werkzeug.security import generate_password_hash, check_password_hash
import json, io, os
from datetime import datetime
from pdf_generator import build_pdf

# ── App setup ──────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///cv_generator.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = "index"

# ── Models ─────────────────────────────────────────────────────────────────
class User(UserMixin, db.Model):
    id           = db.Column(db.Integer, primary_key=True)
    email        = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    cvs          = db.relationship("CV", backref="owner", lazy=True,
                                   cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class CV(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    title      = db.Column(db.String(120), nullable=False, default="Curriculum")
    data       = db.Column(db.Text, nullable=False)   # JSON blob
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id":         self.id,
            "title":      self.title,
            "data":       json.loads(self.data),
            "created_at": self.created_at.strftime("%d/%m/%Y %H:%M"),
            "updated_at": self.updated_at.strftime("%d/%m/%Y %H:%M"),
        }


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# ── Auth routes ────────────────────────────────────────────────────────────
@app.route("/auth/register", methods=["POST"])
def register():
    body = request.get_json()
    email    = (body.get("email") or "").strip().lower()
    password = body.get("password") or ""
    if not email or not password:
        return jsonify({"error": "Email e password obbligatorie"}), 400
    if len(password) < 6:
        return jsonify({"error": "La password deve essere di almeno 6 caratteri"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email già registrata"}), 409
    user = User(email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    login_user(user, remember=True)
    return jsonify({"ok": True, "email": user.email})


@app.route("/auth/login", methods=["POST"])
def login():
    body = request.get_json()
    email    = (body.get("email") or "").strip().lower()
    password = body.get("password") or ""
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Credenziali non valide"}), 401
    login_user(user, remember=True)
    return jsonify({"ok": True, "email": user.email})


@app.route("/auth/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return jsonify({"ok": True})


@app.route("/auth/me")
def me():
    if current_user.is_authenticated:
        return jsonify({"logged_in": True, "email": current_user.email})
    return jsonify({"logged_in": False})


# ── CV CRUD ────────────────────────────────────────────────────────────────
@app.route("/api/cvs", methods=["GET"])
@login_required
def list_cvs():
    cvs = CV.query.filter_by(user_id=current_user.id)\
                  .order_by(CV.updated_at.desc()).all()
    # Exclude photo from list to keep payload small
    result = []
    for cv in cvs:
        d = cv.to_dict()
        d["data"].pop("photo", None)   # strip photo from list
        result.append(d)
    return jsonify(result)


@app.route("/api/cvs", methods=["POST"])
@login_required
def save_cv():
    body     = request.get_json()
    cv_data  = body.get("data", {})
    cv_title = body.get("title") or cv_data.get("name") or "Curriculum"
    cv_id    = body.get("id")

    if cv_id:
        cv = CV.query.filter_by(id=cv_id, user_id=current_user.id).first()
        if not cv:
            return jsonify({"error": "CV non trovato"}), 404
        cv.title      = cv_title
        cv.data       = json.dumps(cv_data)
        cv.updated_at = datetime.utcnow()
    else:
        cv = CV(user_id=current_user.id,
                title=cv_title,
                data=json.dumps(cv_data))
        db.session.add(cv)

    db.session.commit()
    return jsonify({"ok": True, "id": cv.id, "title": cv.title,
                    "updated_at": cv.updated_at.strftime("%d/%m/%Y %H:%M")})


@app.route("/api/cvs/<int:cv_id>", methods=["GET"])
@login_required
def load_cv(cv_id):
    cv = CV.query.filter_by(id=cv_id, user_id=current_user.id).first_or_404()
    return jsonify(cv.to_dict())


@app.route("/api/cvs/<int:cv_id>", methods=["DELETE"])
@login_required
def delete_cv(cv_id):
    cv = CV.query.filter_by(id=cv_id, user_id=current_user.id).first_or_404()
    db.session.delete(cv)
    db.session.commit()
    return jsonify({"ok": True})


# ── Existing routes ────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/preview", methods=["POST"])
def preview():
    data     = request.get_json()
    template = data.get("template", "classic")
    return render_template(f"cv_{template}.html", d=data)


@app.route("/download", methods=["POST"])
def download():
    data     = request.get_json()
    template = data.get("template", "classic")
    buf      = build_pdf(data, template)
    name     = (data.get("name") or "curriculum").lower().replace(" ", "-")
    return send_file(buf, mimetype="application/pdf",
                     as_attachment=True,
                     download_name=f"{name}.pdf")


# ── Bootstrap ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
