# Flask Patterns Reference

Common patterns and best practices for Flask web applications.

## Application Factory

```python
# app/__init__.py
from flask import Flask

def create_app(config_name: str = "default") -> Flask:
    """Application factory."""
    app = Flask(__name__)

    # Load config
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)

    # Register blueprints
    from app.main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from app.api import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix="/api")

    return app
```

## Blueprints

```python
# app/main/__init__.py
from flask import Blueprint

main = Blueprint("main", __name__)

from app.main import routes  # noqa: E402, F401
```

```python
# app/main/routes.py
from flask import render_template
from app.main import main

@main.route("/")
def index():
    return render_template("index.html")

@main.route("/about")
def about():
    return render_template("about.html")
```

## API Patterns

### JSON Responses

```python
from flask import jsonify, request

@app.route("/api/items", methods=["GET"])
def get_items():
    items = Item.query.all()
    return jsonify([item.to_dict() for item in items])

@app.route("/api/items", methods=["POST"])
def create_item():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    item = Item(**data)
    db.session.add(item)
    db.session.commit()

    return jsonify(item.to_dict()), 201

@app.route("/api/items/<int:item_id>", methods=["GET"])
def get_item(item_id: int):
    item = Item.query.get_or_404(item_id)
    return jsonify(item.to_dict())
```

### Error Handling

```python
from flask import jsonify

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({"error": "Internal server error"}), 500
```

## Templates

### Base Template

```html
<!-- templates/base.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}{% endblock %} - MyApp</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
    {% block styles %}{% endblock %}
</head>
<body>
    <nav>
        <a href="{{ url_for('main.index') }}">Home</a>
        <a href="{{ url_for('main.about') }}">About</a>
    </nav>

    <main>
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        {% block content %}{% endblock %}
    </main>

    <script src="{{ url_for('static', filename='js/main.js') }}"></script>
    {% block scripts %}{% endblock %}
</body>
</html>
```

### Child Template

```html
<!-- templates/index.html -->
{% extends "base.html" %}

{% block title %}Home{% endblock %}

{% block content %}
<h1>Welcome</h1>
<p>Hello, {{ name }}!</p>

{% for item in items %}
    <div class="item">
        <h2>{{ item.title }}</h2>
        <p>{{ item.description }}</p>
    </div>
{% else %}
    <p>No items found.</p>
{% endfor %}
{% endblock %}
```

## Forms with Flask-WTF

```python
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length

class ContactForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=100)])
    message = TextAreaField("Message", validators=[DataRequired()])
    submit = SubmitField("Send")
```

```python
@app.route("/contact", methods=["GET", "POST"])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        # Process form
        flash("Message sent!", "success")
        return redirect(url_for("main.index"))
    return render_template("contact.html", form=form)
```

## Database with Flask-SQLAlchemy

```python
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    posts = db.relationship("Post", backref="author", lazy=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
        }

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
```

## Configuration

```python
# config.py
import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-key-change-in-prod"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///dev.db"

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")

config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
```

## Testing

```python
# tests/conftest.py
import pytest
from app import create_app, db

@pytest.fixture
def app():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

# tests/test_routes.py
def test_index(client):
    response = client.get("/")
    assert response.status_code == 200

def test_api_items(client):
    response = client.get("/api/items")
    assert response.status_code == 200
    assert response.json == []
```

## Deployment

### Gunicorn

```bash
# Install
uv add gunicorn

# Run
uv run gunicorn -w 4 -b 0.0.0.0:8000 "app:create_app()"
```

### Docker

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy project
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .

EXPOSE 8000
CMD ["uv", "run", "gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app:create_app()"]
```
