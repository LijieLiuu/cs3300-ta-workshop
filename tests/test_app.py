import pytest

from app import app, tasks


@pytest.fixture
def client():
    """Provide a Flask test client."""
    app.config['TESTING'] = True
    with app.test_client() as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_tasks():
    """Reset the in-memory task collection before each test."""
    tasks.clear()
    tasks.extend([
        {"id": 1, "title": "Project-1 Report"},
        {"id": 2, "title": "Project-2 MMFs"}
    ])


def test_index(client):
    """Render the task tracker page."""
    response = client.get('/')
    assert response.status_code == 200
    assert b"Task Tracker" in response.data


def test_get_tasks(client):
    """Return all existing tasks from the API."""
    response = client.get('/api/tasks')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 2


def test_get_tasks_returns_medium_for_legacy_tasks(client):
    """Return Medium for tasks created before priority was supported."""
    response = client.get('/api/tasks')
    data = response.get_json()

    assert response.status_code == 200
    assert all(task['priority'] == 'Medium' for task in data)


def test_get_tasks_returns_existing_priorities(client):
    """Preserve and return priorities already stored on tasks."""
    tasks.append({
        "id": 3,
        "title": "High priority task",
        "priority": "High"
    })

    response = client.get('/api/tasks')
    data = response.get_json()

    assert response.status_code == 200
    assert data[-1]['priority'] == 'High'


def test_add_task_defaults_to_medium_priority(client):
    """Default a task without a priority to Medium."""
    response = client.post('/api/tasks', json={"title": "Test new task"})

    assert response.status_code == 201
    assert response.get_json()['priority'] == 'Medium'


def test_add_task_defaults_empty_priority_to_medium(client):
    """Default an empty priority value to Medium."""
    response = client.post(
        '/api/tasks',
        json={"title": "Task with empty priority", "priority": ""}
    )

    assert response.status_code == 201
    assert response.get_json()['priority'] == 'Medium'


@pytest.mark.parametrize('priority', ['Low', 'Medium', 'High'])
def test_add_task_accepts_valid_priorities(client, priority):
    """Create tasks with each supported priority value."""
    response = client.post(
        '/api/tasks',
        json={"title": f"{priority} task", "priority": priority}
    )

    assert response.status_code == 201
    assert response.get_json()['priority'] == priority


@pytest.mark.parametrize('priority', ['Urgent', 'low', 1, ['High']])
def test_add_task_rejects_invalid_priorities(client, priority):
    """Reject priority values outside the supported set."""
    response = client.post(
        '/api/tasks',
        json={"title": "Invalid priority task", "priority": priority}
    )

    assert response.status_code == 400
    assert 'error' in response.get_json()


def test_add_task_missing_title(client):
    """Reject task creation requests without a title."""
    response = client.post('/api/tasks', json={"wrong_key": "value"})
    assert response.status_code == 400
    assert "error" in response.get_json()

    response = client.post('/api/tasks', json={})
    assert response.status_code == 400


def test_delete_task(client):
    """Delete an existing task."""
    response = client.delete('/api/tasks/1')
    assert response.status_code == 200
    get_response = client.get('/api/tasks')
    data = get_response.get_json()
    assert len(data) == 1
    assert data[0]['id'] == 2
