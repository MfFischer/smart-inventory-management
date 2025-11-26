"""
Basic tests for the updated routes and templates.
"""
import pytest
from inventory_system import create_app
from inventory_system.extensions import db
from modules.models.users import User


@pytest.fixture
def app():
    """Create and configure a test app instance."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()


@pytest.fixture
def authenticated_client(app, client):
    """Create an authenticated test client."""
    with app.app_context():
        # Create a test user
        user = User(
            username='testuser',
            email='test@example.com',
            role='admin'
        )
        user.set_password('testpassword')
        db.session.add(user)
        db.session.commit()
        
        # Login
        client.post('/login', data={
            'username': 'testuser',
            'password': 'testpassword'
        }, follow_redirects=True)
        
        yield client


class TestPublicRoutes:
    """Test public routes (no authentication required)."""
    
    def test_landing_page(self, client):
        """Test landing page loads correctly."""
        response = client.get('/')
        assert response.status_code == 200
        assert b'BMSgo' in response.data or b'Run Your Business' in response.data
    
    def test_login_page(self, client):
        """Test login page loads correctly."""
        response = client.get('/login')
        assert response.status_code == 200
        assert b'Welcome Back' in response.data or b'Sign in' in response.data
    
    def test_register_page(self, client):
        """Test registration page loads correctly."""
        response = client.get('/register')
        assert response.status_code == 200
        assert b'Free Trial' in response.data or b'Register' in response.data
    
    def test_index_redirect(self, client):
        """Test deprecated /index route redirects."""
        response = client.get('/index')
        assert response.status_code == 302  # Redirect


class TestAuthenticatedRoutes:
    """Test authenticated routes (require login)."""
    
    def test_dashboard_access(self, authenticated_client):
        """Test dashboard is accessible when authenticated."""
        response = authenticated_client.get('/personal_dashboard')
        assert response.status_code == 200
        assert b'Dashboard' in response.data or b'Welcome back' in response.data
    
    def test_dashboard_redirect_when_not_authenticated(self, client):
        """Test dashboard redirects to login when not authenticated."""
        response = client.get('/personal_dashboard')
        assert response.status_code == 302  # Redirect to login


class TestTemplateRendering:
    """Test that templates render without errors."""
    
    def test_landing_template_structure(self, client):
        """Test landing page has expected structure."""
        response = client.get('/')
        assert response.status_code == 200
        # Check for key sections
        data = response.data.decode('utf-8')
        assert 'BMSgo' in data or 'Smart' in data
    
    def test_login_template_structure(self, client):
        """Test login page has expected structure."""
        response = client.get('/login')
        assert response.status_code == 200
        data = response.data.decode('utf-8')
        assert 'username' in data.lower()
        assert 'password' in data.lower()
    
    def test_register_template_structure(self, client):
        """Test registration page has expected structure."""
        response = client.get('/register')
        assert response.status_code == 200
        data = response.data.decode('utf-8')
        assert 'username' in data.lower()
        assert 'email' in data.lower()
        assert 'password' in data.lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

