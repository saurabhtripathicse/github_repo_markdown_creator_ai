#!/usr/bin/env python3
"""
Flask Usage Documentation Fixer

This script creates a comprehensive USAGE.md file for Flask with complete code examples.
"""

import os

# Create output directory if it doesn't exist
output_dir = "output/flask"
os.makedirs(output_dir, exist_ok=True)

# Define the complete Flask usage documentation with detailed examples
FLASK_USAGE_DOC = """# Flask Usage Guide

Flask is a lightweight WSGI web application framework designed to make getting started quick and easy, with the ability to scale up to complex applications. This guide will help you install Flask, get started with basic and advanced usage, configure your application, and troubleshoot common issues.

## Installation

To install Flask, you need to have Python installed on your system. You can install Flask using pip, the Python package manager. Follow the steps below:

### Using pip

To install Flask using pip, run the following command:

```bash
pip install Flask
```

### Using pipenv

To manage your dependencies with pipenv, use the following commands:

```bash
pip install pipenv
pipenv install Flask
```

### Using poetry

To use poetry for dependency management, run:

```bash
pip install poetry
poetry add Flask
```

## Basic Usage

This section covers the basics of creating a Flask application, routing, handling HTTP methods, rendering templates, and working with static files.

### Creating a Basic Flask Application

Here's a simple example of a Flask application that returns "Hello, World!" when accessed at the root URL:

```python
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, World!'

if __name__ == '__main__':
    app.run(debug=True)
```

Save this code in a file named `app.py` and run it with `python app.py`. Then, open your browser and navigate to `http://127.0.0.1:5000/` to see "Hello, World!".

### Routing and URL Building

Flask allows you to define routes for different URLs. Here's how you can set up various routes:

```python
from flask import Flask, url_for

app = Flask(__name__)

@app.route('/')
def index():
    return 'Index Page'

@app.route('/hello')
def hello():
    return 'Hello, World'

@app.route('/user/<username>')
def show_user_profile(username):
    # show the user profile for that user
    return f'User {username}'

@app.route('/post/<int:post_id>')
def show_post(post_id):
    # show the post with the given id, the id is an integer
    return f'Post {post_id}'

@app.route('/path/<path:subpath>')
def show_subpath(subpath):
    # show the subpath after /path/
    return f'Subpath {subpath}'

# URL building example
@app.route('/url_building')
def url_building_example():
    # Generate URLs for different routes
    with app.test_request_context():
        print(url_for('index'))                    # /
        print(url_for('hello'))                    # /hello
        print(url_for('show_user_profile', username='John'))  # /user/John
        print(url_for('show_post', post_id=5))     # /post/5
        print(url_for('static', filename='style.css'))  # /static/style.css
    return 'Check console for URL examples'

if __name__ == '__main__':
    app.run(debug=True)
```

### Handling HTTP Methods (GET, POST)

Flask makes it easy to handle different HTTP methods. Here's an example of a login form that handles both GET and POST requests:

```python
from flask import Flask, request, redirect, url_for, render_template

app = Flask(__name__)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Process the login form
        username = request.form['username']
        password = request.form['password']
        # Validate credentials
        if validate_login(username, password):
            return redirect(url_for('dashboard'))
        else:
            return 'Invalid credentials'
    else:
        # Show the login form
        return '''
            <form method="post">
                <p><input type="text" name="username" placeholder="Username"></p>
                <p><input type="password" name="password" placeholder="Password"></p>
                <p><input type="submit" value="Login"></p>
            </form>
        '''

def validate_login(username, password):
    # This would typically check against a database
    return username == 'admin' and password == 'password'

@app.route('/dashboard')
def dashboard():
    return 'Welcome to the dashboard!'

if __name__ == '__main__':
    app.run(debug=True)
```

### Rendering Templates

Flask supports Jinja2 templating. Here's how you can render a template:

```python
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/hello/')
@app.route('/hello/<name>')
def hello(name=None):
    return render_template('hello.html', name=name)

if __name__ == '__main__':
    app.run(debug=True)
```

For this to work, you need to create a `templates` folder in the same directory as your application and add a file named `hello.html` with the following content:

```html
<!doctype html>
<html>
  <head>
    <title>Hello from Flask</title>
  </head>
  <body>
    {% if name %}
      <h1>Hello {{ name }}!</h1>
    {% else %}
      <h1>Hello, World!</h1>
    {% endif %}
  </body>
</html>
```

### Working with Static Files

Flask automatically serves static files from the `static` folder. Here's how you can include static files in your templates:

```python
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
```

Create a `static` folder in the same directory as your application and add a file named `style.css`. Then, create a `templates` folder and add a file named `index.html` with the following content:

```html
<!doctype html>
<html>
  <head>
    <title>Flask Static Files</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
  </head>
  <body>
    <h1>Static Files Example</h1>
    <p>This page includes a CSS file from the static folder.</p>
  </body>
</html>
```

## Advanced Usage

Explore more complex use cases, including application structure, extensions, databases, authentication, RESTful APIs, error handling, and testing.

### Blueprints for Application Structure

Blueprints help organize your application into modules. Here's an example:

```python
# auth.py
from flask import Blueprint, render_template, redirect, url_for, request, flash

auth = Blueprint('auth', __name__)

@auth.route('/login')
def login():
    return render_template('login.html')

@auth.route('/signup')
def signup():
    return render_template('signup.html')

@auth.route('/logout')
def logout():
    return redirect(url_for('main.index'))

# main.py
from flask import Blueprint, render_template

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/profile')
def profile():
    return render_template('profile.html')

# app.py
from flask import Flask

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your-secret-key'
    
    from auth import auth
    from main import main
    
    app.register_blueprint(auth)
    app.register_blueprint(main, url_prefix='/')
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
```

### Flask Extensions and How to Use Them

Flask extensions add functionality to your application. Here's an example using Flask-SQLAlchemy:

```python
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///example.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
```

### Working with Databases (SQLAlchemy)

Flask-SQLAlchemy simplifies database interactions. Here's a CRUD example:

```python
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///example.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat()
        }

@app.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    
    if not data or not 'username' in data or not 'email' in data:
        return jsonify({'error': 'Missing required fields'}), 400
    
    user = User(username=data['username'], email=data['email'])
    
    try:
        db.session.add(user)
        db.session.commit()
        return jsonify(user.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])

@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())

@app.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    if 'username' in data:
        user.username = data['username']
    if 'email' in data:
        user.email = data['email']
    
    try:
        db.session.commit()
        return jsonify(user.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    try:
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': f'User {user_id} deleted'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
```

### Authentication and Authorization

Flask-Login provides user session management. Here's a basic example:

```python
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # Replace with a real secret key in production

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Simple user model for demonstration
class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash

# In-memory user database for demonstration
users = {
    1: User(1, 'user1', generate_password_hash('password1')),
    2: User(2, 'user2', generate_password_hash('password2'))
}

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return users.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Find user by username
        user = next((u for u in users.values() if u.username == username), None)
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        
        flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

if __name__ == '__main__':
    app.run(debug=True)
```

### RESTful API Development

Flask-RESTful simplifies API development. Here's an example:

```python
from flask import Flask, request, jsonify
from flask_restful import Resource, Api, reqparse
from werkzeug.exceptions import BadRequest, NotFound

app = Flask(__name__)
api = Api(app)

# In-memory database for demonstration
ITEMS = {
    1: {"name": "Laptop", "price": 999.99},
    2: {"name": "Smartphone", "price": 499.99},
    3: {"name": "Headphones", "price": 149.99}
}

class ItemResource(Resource):
    def get(self, item_id):
        item = ITEMS.get(item_id)
        if item is None:
            raise NotFound(f"Item with id {item_id} not found")
        return item
    
    def put(self, item_id):
        if item_id not in ITEMS:
            raise NotFound(f"Item with id {item_id} not found")
        
        data = request.get_json()
        if not data:
            raise BadRequest("No input data provided")
        
        if "name" in data:
            ITEMS[item_id]["name"] = data["name"]
        if "price" in data:
            ITEMS[item_id]["price"] = data["price"]
        
        return ITEMS[item_id]
    
    def delete(self, item_id):
        if item_id not in ITEMS:
            raise NotFound(f"Item with id {item_id} not found")
        
        del ITEMS[item_id]
        return {"message": f"Item with id {item_id} deleted"}

class ItemListResource(Resource):
    def get(self):
        return list(ITEMS.values())
    
    def post(self):
        data = request.get_json()
        if not data or "name" not in data or "price" not in data:
            raise BadRequest("Name and price are required")
        
        item_id = max(ITEMS.keys()) + 1 if ITEMS else 1
        ITEMS[item_id] = {
            "name": data["name"],
            "price": data["price"]
        }
        
        return ITEMS[item_id], 201

api.add_resource(ItemListResource, '/items')
api.add_resource(ItemResource, '/items/<int:item_id>')

if __name__ == '__main__':
    app.run(debug=True)
```

### Error Handling and Logging

Flask provides mechanisms for error handling and logging. Here's how you can handle errors:

```python
from flask import Flask, render_template, jsonify
import logging

app = Flask(__name__)

# Configure logging
handler = logging.FileHandler('app.log')
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)

class APIError(Exception):
    status_code = 400
    
    def __init__(self, message, status_code=None, payload=None):
        super().__init__()
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload
    
    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv

@app.errorhandler(404)
def page_not_found(e):
    # Log the error
    app.logger.error(f"404 error: {request.path}")
    # For HTML responses
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    # Log the error
    app.logger.error(f"500 error: {str(e)}")
    # For HTML responses
    return render_template('500.html'), 500

@app.errorhandler(APIError)
def handle_api_error(error):
    # Log the error
    app.logger.error(f"API error: {error.message}")
    # For API responses
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

@app.route('/api/resource')
def get_resource():
    # Example of raising a custom API error
    app.logger.info("Resource requested")
    raise APIError('Resource not available', status_code=503)

@app.route('/api/item/<int:item_id>')
def get_item(item_id):
    app.logger.info(f"Item requested: {item_id}")
    
    if item_id <= 0:
        raise APIError('Invalid item ID', status_code=400)
    
    # Simulate item not found
    if item_id > 100:
        raise APIError('Item not found', status_code=404)
    
    return jsonify({'id': item_id, 'name': f'Item {item_id}'})

if __name__ == '__main__':
    app.run(debug=True)
```

### Testing Flask Applications

Testing is crucial for maintaining application quality. Here's how you can test a Flask application using pytest:

```python
# app.py
from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/api/greeting')
def greeting():
    name = request.args.get('name', 'World')
    return jsonify({'message': f'Hello, {name}!'})

@app.route('/api/add', methods=['POST'])
def add_numbers():
    data = request.get_json()
    if not data or 'a' not in data or 'b' not in data:
        return jsonify({'error': 'Missing required parameters'}), 400
    
    try:
        a = float(data['a'])
        b = float(data['b'])
        return jsonify({'result': a + b})
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid number format'}), 400

if __name__ == '__main__':
    app.run(debug=True)

# test_app.py
import pytest
import json
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_greeting_default(client):
    response = client.get('/api/greeting')
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['message'] == 'Hello, World!'

def test_greeting_with_name(client):
    response = client.get('/api/greeting?name=Flask')
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['message'] == 'Hello, Flask!'

def test_add_numbers_valid(client):
    response = client.post(
        '/api/add',
        data=json.dumps({'a': 5, 'b': 3}),
        content_type='application/json'
    )
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['result'] == 8

def test_add_numbers_invalid(client):
    response = client.post(
        '/api/add',
        data=json.dumps({'a': 'invalid', 'b': 3}),
        content_type='application/json'
    )
    assert response.status_code == 400
    json_data = response.get_json()
    assert 'error' in json_data

# Run tests with: pytest test_app.py
```

## Configuration

Flask applications can be configured in various ways. This section covers configuration options and best practices.

### Configuration from Files

You can load configuration from Python files or environment variables:

```python
from flask import Flask

app = Flask(__name__)

# Load config from a Python file
app.config.from_pyfile('config.py')

# Or use environment variables
app.config.from_envvar('APP_CONFIG')

# Access configuration values
secret_key = app.config['SECRET_KEY']
debug = app.config['DEBUG']

@app.route('/')
def index():
    return f'App is running with DEBUG={debug}'

if __name__ == '__main__':
    app.run()
```

Example `config.py` file:

```python
DEBUG = True
SECRET_KEY = 'your-secret-key'
DATABASE_URI = 'sqlite:///app.db'
```

### Environment Variables

You can use environment variables for configuration, especially in production:

```python
import os
from flask import Flask

app = Flask(__name__)

# Load configuration from environment variables
app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', 'False') == 'True'
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'default-secret-key')
app.config['DATABASE_URI'] = os.environ.get('DATABASE_URI', 'sqlite:///app.db')

@app.route('/')
def index():
    return f'App is running with DEBUG={app.config["DEBUG"]}'

if __name__ == '__main__':
    app.run()
```

### Instance Folders

Flask provides an instance folder for configuration files that shouldn't be in version control:

```python
from flask import Flask

app = Flask(__name__, instance_relative_config=True)

# Load default config
app.config.from_object('config.default')

# Load instance config (overrides default config)
app.config.from_pyfile('config.py', silent=True)

@app.route('/')
def index():
    return f'App is running with DEBUG={app.config["DEBUG"]}'

if __name__ == '__main__':
    app.run()
```

### Application Factories

Application factories allow you to create multiple instances of your application with different configurations:

```python
from flask import Flask

def create_app(config_name='default'):
    app = Flask(__name__, instance_relative_config=True)
    
    # Load default configuration
    if config_name == 'default':
        app.config.from_object('config.default')
    elif config_name == 'development':
        app.config.from_object('config.development')
    elif config_name == 'production':
        app.config.from_object('config.production')
    elif config_name == 'testing':
        app.config.from_object('config.testing')
    
    # Load instance configuration
    app.config.from_pyfile('config.py', silent=True)
    
    # Register blueprints
    from auth import auth_bp
    from main import main_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    
    return app

if __name__ == '__main__':
    app = create_app('development')
    app.run()
```

## Deployment

This section covers options for deploying Flask applications in development and production environments.

### Development Server

Flask comes with a built-in development server, which is great for development but not suitable for production:

```python
from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return 'Hello, World!'

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
```

### Production Deployment with Gunicorn

For production, you should use a WSGI server like Gunicorn:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

Where `app:app` refers to the Flask application instance in your `app.py` file.

### Containerization with Docker

You can containerize your Flask application using Docker:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_APP=app.py
ENV FLASK_ENV=production

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

Build and run the Docker container:

```bash
docker build -t flask-app .
docker run -p 5000:5000 flask-app
```

### Cloud Deployment

You can deploy Flask applications to various cloud platforms:

#### Heroku

Create a `Procfile` in your project root:

```
web: gunicorn app:app
```

And deploy to Heroku:

```bash
heroku create
git push heroku main
```

#### AWS Elastic Beanstalk

Create a `.ebextensions` directory with a `python.config` file:

```yaml
option_settings:
  aws:elasticbeanstalk:container:python:
    WSGIPath: app:app
```

And deploy to Elastic Beanstalk:

```bash
eb init
eb create
```

## Troubleshooting

This section covers common issues and their solutions when working with Flask.

### Common Issues

#### 1. Application Not Starting

If your application fails to start, check:
- Syntax errors in your code
- Missing dependencies
- Port conflicts (another application might be using the same port)

#### 2. 404 Not Found Errors

If you're getting 404 errors:
- Check your route definitions
- Ensure the URL you're accessing matches a defined route
- Check for typos in the URL

#### 3. 500 Internal Server Errors

If you're getting 500 errors:
- Check your application logs for error details
- Look for exceptions in your code
- Verify database connections and credentials

#### 4. Static Files Not Loading

If static files aren't loading:
- Ensure your static folder is correctly configured
- Check file paths in your templates
- Verify file permissions

#### 5. Database Connection Issues

If you're having database connection problems:
- Verify your database URI
- Check database credentials
- Ensure the database server is running
- Check network connectivity

### Debugging Tips

#### Enable Debug Mode

Debug mode provides detailed error messages and an interactive debugger:

```python
app.config['DEBUG'] = True
```

#### Use Logging

Add logging to your application to track issues:

```python
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

app.logger.debug('Debug message')
app.logger.info('Info message')
app.logger.warning('Warning message')
app.logger.error('Error message')
```

#### Flask Debug Toolbar

The Flask Debug Toolbar provides additional debugging information:

```bash
pip install flask-debugtoolbar
```

```python
from flask import Flask
from flask_debugtoolbar import DebugToolbarExtension

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

toolbar = DebugToolbarExtension(app)

@app.route('/')
def index():
    return 'Hello, World!'

if __name__ == '__main__':
    app.run(debug=True)
```

## Conclusion

Flask is a powerful and flexible web framework that allows you to build everything from simple websites to complex web applications and APIs. This guide covered the basics of installation, usage, configuration, deployment, and troubleshooting. For more information, refer to the [official Flask documentation](https://flask.palletsprojects.com/).
"""

# Write the documentation to file
usage_file_path = os.path.join(output_dir, "USAGE.md")
with open(usage_file_path, 'w', encoding='utf-8') as f:
    f.write(FLASK_USAGE_DOC)

print(f"Successfully created comprehensive Flask usage documentation at {usage_file_path}")
