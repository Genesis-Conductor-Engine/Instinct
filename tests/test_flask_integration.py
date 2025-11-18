"""
Tests for Flask app integration with aurora_orchestrator.

This module tests the Flask web application that serves files generated
by the A.U.R.O.R.A. orchestrator.
"""
import pytest
from pathlib import Path
import sys

# Add parent directory to path to import flask_app
sys.path.insert(0, str(Path(__file__).parent.parent))

from flask_app import app
from aurora_orchestrator import PROJECT_STATE


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_dashboard_loads(client):
    """Test that the dashboard page loads successfully."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'A.U.R.O.R.A. Orchestrator Dashboard' in response.data


def test_api_state_endpoint(client):
    """Test that the /api/state endpoint returns project state."""
    response = client.get('/api/state')
    assert response.status_code == 200
    data = response.get_json()
    assert 'tasks' in data
    assert 'codebase' in data
    assert 'design_system' in data
    assert 'message_bus' in data


def test_api_files_endpoint(client):
    """Test that the /api/files endpoint returns file list."""
    response = client.get('/api/files')
    assert response.status_code == 200
    data = response.get_json()
    assert 'files' in data
    assert 'count' in data
    assert isinstance(data['files'], dict)
    assert data['count'] == len(data['files'])


def test_view_existing_file(client):
    """Test viewing a file that exists in the codebase."""
    # Get the first file from PROJECT_STATE
    if PROJECT_STATE['codebase']['files']:
        file_path = list(PROJECT_STATE['codebase']['files'].keys())[0]
        response = client.get(f'/files/{file_path}')
        assert response.status_code == 200
        # Check that the file content is displayed
        file_content = PROJECT_STATE['codebase']['files'][file_path]
        assert file_content.encode() in response.data


def test_view_nonexistent_file(client):
    """Test that viewing a non-existent file returns 404."""
    response = client.get('/files/nonexistent/file.txt')
    assert response.status_code == 404
    data = response.get_json()
    assert 'error' in data
    assert data['error'] == 'File not found'


def test_dashboard_shows_stats(client):
    """Test that the dashboard displays project statistics."""
    response = client.get('/')
    assert response.status_code == 200
    # Check for stats sections
    assert b'Tasks Completed' in response.data
    assert b'Files Generated' in response.data
    assert b'Messages Posted' in response.data


def test_dashboard_shows_files(client):
    """Test that the dashboard displays generated files."""
    response = client.get('/')
    assert response.status_code == 200
    # Check for files section
    assert b'Generated Files' in response.data
    # If files exist, check they're listed
    if PROJECT_STATE['codebase']['files']:
        for file_path in PROJECT_STATE['codebase']['files'].keys():
            assert file_path.encode() in response.data


def test_dashboard_shows_design_system(client):
    """Test that the dashboard displays design system info."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Design System' in response.data
    # If colors exist, check they're displayed
    if PROJECT_STATE['design_system']['colors']:
        for color_name in PROJECT_STATE['design_system']['colors'].keys():
            assert color_name.encode() in response.data


def test_dashboard_shows_messages(client):
    """Test that the dashboard displays message bus."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Message Bus' in response.data
    # If messages exist, check they're displayed
    if PROJECT_STATE['message_bus']:
        # Check for at least one message
        first_message = PROJECT_STATE['message_bus'][0]
        assert first_message.encode() in response.data


def test_api_endpoints_section(client):
    """Test that the dashboard shows API endpoints."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'API Endpoints' in response.data
    assert b'/api/state' in response.data
    assert b'/api/files' in response.data
