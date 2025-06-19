import pytest
from app import app


def test_index_page(client):
    """Test that the index page loads successfully."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'CyberQuiz' in response.data or b'Welcome' in response.data


def test_login_page_get(client):
    """Test that the login page loads successfully."""
    response = client.get('/login')
    assert response.status_code == 200
    assert b'email' in response.data.lower()


def test_404_page(client):
    """Test that 404 page works."""
    response = client.get('/nonexistent-page')
    assert response.status_code == 404


def test_dashboard_redirect_when_not_logged_in(client):
    """Test that dashboard redirects to login when user is not logged in."""
    response = client.get('/dashboard')
    assert response.status_code == 302
    assert '/login' in response.location


def test_admin_unauthorized_access(client):
    """Test that admin page blocks unauthorized access."""
    response = client.get('/admin')
    assert response.status_code == 302
    assert '/' in response.location