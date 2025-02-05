# Task Manager API Demo

A Django REST framework demo project showcasing a task management API with priority scoring and unit tests.

## Features

- RESTful API for task management
- Priority scoring system based on task urgency and importance
- Utility functions for task prioritization and overdue detection
- Comprehensive pytest test suite
- Docker support for easy deployment

## Project Structure

```
taskmanager/
├── tasks/                 # Main app directory
│   ├── models.py         # Task model definition
│   ├── utils.py          # Utility functions for task management
│   ├── views.py          # API views and endpoints
│   ├── serializers.py    # REST framework serializers
│   └── tests/            # Test directory
│       └── test_utils.py # Utility function tests
├── taskmanager/          # Project settings
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── pytest.ini
```

## API Endpoints

- `GET /api/tasks/` - List all tasks
- `POST /api/tasks/` - Create a new task
- `GET /api/tasks/{id}/` - Retrieve a specific task
- `PUT /api/tasks/{id}/` - Update a task
- `DELETE /api/tasks/{id}/` - Delete a task
- `GET /api/tasks/prioritized/` - Get tasks sorted by priority score
- `GET /api/tasks/overdue/` - Get overdue tasks

## Running with Docker

1. Build and start the containers:

   ```bash
   docker-compose up --build
   ```

2. Run migrations:
   ```bash
   docker-compose exec web python manage.py migrate
   ```

## Running Tests

```bash
docker-compose exec web pytest
```

## Task Priority Scoring

The `TaskUtils` class implements a sophisticated priority scoring system that considers:

- Task priority level (HIGH/MEDIUM/LOW)
- Due date proximity
- Overdue status

Higher scores indicate higher priority tasks that should be addressed first.
