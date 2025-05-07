#!/usr/bin/env python3
"""
Flask Usage Documentation Generator

This script generates a comprehensive USAGE.md file for Flask with detailed code examples.
"""

import os
import sys
import logging
import requests
import json
from typing import Dict, Any, List
from dotenv import load_dotenv
from openai import OpenAI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('flask_usage_generator')

# Load environment variables
load_dotenv()

# Constants
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Flask-specific examples to include
FLASK_EXAMPLES = [
    {
        "title": "Basic Flask Application",
        "code": """
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, World!'

if __name__ == '__main__':
    app.run(debug=True)
"""
    },
    {
        "title": "Flask Routing",
        "code": """
from flask import Flask

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

if __name__ == '__main__':
    app.run(debug=True)
"""
    },
    {
        "title": "HTTP Methods",
        "code": """
from flask import Flask, request, redirect, url_for

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
                <p><input type="text" name="username"></p>
                <p><input type="password" name="password"></p>
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
"""
    },
    {
        "title": "Templates",
        "code": """
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/hello/')
@app.route('/hello/<name>')
def hello(name=None):
    return render_template('hello.html', name=name)

# Example hello.html template:
# <!doctype html>
# <title>Hello from Flask</title>
# {% if name %}
#   <h1>Hello {{ name }}!</h1>
# {% else %}
#   <h1>Hello, World!</h1>
# {% endif %}

if __name__ == '__main__':
    app.run(debug=True)
"""
    },
    {
        "title": "Request Object",
        "code": """
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/api/data', methods=['POST'])
def process_data():
    # Get JSON data from request
    data = request.get_json()
    
    # Get form data
    # form_data = request.form
    
    # Get URL parameters
    # args = request.args
    
    # Get cookies
    # cookies = request.cookies
    
    # Get headers
    # headers = request.headers
    
    # Process the data (example)
    result = {
        'received': data,
        'status': 'success',
        'message': 'Data processed successfully'
    }
    
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
"""
    },
    {
        "title": "Blueprints",
        "code": """
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
    
    from auth import auth
    from main import main
    
    app.register_blueprint(auth)
    app.register_blueprint(main)
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
"""
    },
    {
        "title": "Database with Flask-SQLAlchemy",
        "code": """
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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
"""
    },
    {
        "title": "Flask REST API",
        "code": """
from flask import Flask, request, jsonify
from flask_restful import Resource, Api
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
"""
    },
    {
        "title": "Flask Authentication with Flask-Login",
        "code": """
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
            return redirect(url_for('dashboard'))
        
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

if __name__ == '__main__':
    app.run(debug=True)
"""
    },
    {
        "title": "Flask Error Handling",
        "code": """
from flask import Flask, render_template, jsonify

app = Flask(__name__)

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
    # For HTML responses
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    # For HTML responses
    return render_template('500.html'), 500

@app.errorhandler(APIError)
def handle_api_error(error):
    # For API responses
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

@app.route('/api/resource')
def get_resource():
    # Example of raising a custom API error
    raise APIError('Resource not available', status_code=503)

@app.route('/api/item/<int:item_id>')
def get_item(item_id):
    if item_id <= 0:
        raise APIError('Invalid item ID', status_code=400)
    
    # Simulate item not found
    if item_id > 100:
        raise APIError('Item not found', status_code=404)
    
    return jsonify({'id': item_id, 'name': f'Item {item_id}'})

if __name__ == '__main__':
    app.run(debug=True)
"""
    },
    {
        "title": "Flask Testing",
        "code": """
# app.py
from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/api/greeting')
def greeting():
    name = request.args.get('name', 'World')
    return jsonify({'message': f'Hello, {name}!'})

if __name__ == '__main__':
    app.run(debug=True)

# test_app.py
import pytest
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

# Run tests with: pytest test_app.py
"""
    }
]

def generate_flask_usage_doc() -> str:
    """
    Generate a comprehensive Flask usage documentation with detailed code examples
    
    Returns:
        Generated usage documentation
    """
    logger.info("Generating Flask usage documentation")
    
    # Prepare system prompt
    system_prompt = """
    You are a senior Python developer and technical writer creating a comprehensive USAGE.md file for Flask.
    Your task is to create detailed, practical usage examples and instructions for Flask.
    
    Use markdown with proper formatting:
    - Use a single `#` for the document title
    - Use `##`, `###` for section headers (don't skip levels)
    - Add blank lines before and after headings, lists, code blocks, and tables
    - Use triple-backtick code blocks with language specified
    - Avoid trailing whitespace and punctuation in headings
    
    Include the following sections:
    
    ### Installation
    Step-by-step installation instructions with different options (pip, pipenv, poetry).
    
    ### Basic Usage
    Simple examples to get started quickly, including:
    - Creating a basic Flask application
    - Routing and URL building
    - Handling HTTP methods (GET, POST)
    - Rendering templates
    - Working with static files
    
    ### Advanced Usage
    More complex examples and use cases, including:
    - Blueprints for application structure
    - Flask extensions and how to use them
    - Working with databases (SQLAlchemy)
    - Authentication and authorization
    - RESTful API development
    - Error handling and logging
    - Testing Flask applications
    
    ### Configuration
    Available configuration options and how to use them, including:
    - Configuration from files
    - Environment variables
    - Instance folders
    - Application factories
    
    ### Deployment
    Options for deploying Flask applications, including:
    - Development server
    - Production deployment options (Gunicorn, uWSGI)
    - Containerization with Docker
    - Cloud deployment (Heroku, AWS, etc.)
    
    ### Troubleshooting
    Common issues and their solutions.
    
    Focus on practical, runnable examples. Use the provided code examples and expand on them.
    Be comprehensive and include detailed explanations with each code example.
    Make sure the examples are complete and can be run directly by users.
    """
    
    # Prepare user prompt with code examples
    user_prompt = "I'm creating a comprehensive Flask usage guide with detailed code examples.\n\n"
    
    # Add code examples
    user_prompt += "Here are code examples to include and explain in the documentation:\n\n"
    
    for i, example in enumerate(FLASK_EXAMPLES):
        user_prompt += f"Example {i+1}: {example['title']}\n\n"
        user_prompt += f"```python\n{example['code']}\n```\n\n"
    
    # Generate usage documentation
    try:
        # Use GPT-4 with appropriate token limit
        response = client.chat.completions.create(
            model="gpt-4o",  # Using GPT-4o for better quality
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
            max_tokens=3000  # Adjusted token limit to avoid rate limits
        )
        
        usage_doc = response.choices[0].message.content.strip()
        return f"# Flask Usage Guide\n\n{usage_doc}"
    except Exception as e:
        logger.error(f"Error generating Flask usage documentation: {str(e)}")
        return f"# Error Generating Usage Documentation\n\nAn error occurred while generating the usage documentation: {str(e)}"

def main():
    """
    Main function to generate and save Flask usage documentation
    """
    try:
        # Generate Flask usage documentation
        logger.info("Generating Flask usage documentation")
        usage_doc = generate_flask_usage_doc()
        
        # Create output directory if it doesn't exist
        output_dir = "output/flask"
        os.makedirs(output_dir, exist_ok=True)
        
        # Write documentation to file
        usage_file_path = os.path.join(output_dir, "USAGE.md")
        with open(usage_file_path, 'w', encoding='utf-8') as f:
            f.write(usage_doc)
        
        logger.info(f"Wrote Flask usage documentation to {usage_file_path}")
        print(f"\nSuccessfully generated Flask usage documentation")
        print(f"Documentation file: {usage_file_path}")
        
    except Exception as e:
        logger.error(f"Error generating Flask documentation: {str(e)}")
        import traceback
        traceback.print_exc()
        print(f"\nError: {str(e)}")

if __name__ == "__main__":
    main()
