# Docker Chrome Session Manager

A Python module for managing Selenium Chrome sessions across multiple Docker containers. It provides dynamic container
selection, session configuration persistence, and safe concurrent access for browser automation tasks.

## Features

- **Dynamic Container Management**: Automatically selects available Selenium Chrome containers from a provided list.
- **Session Configuration**: Supports customizable browser settings such as user agent, locale, screen resolution,
  timezone, and additional Chrome options.
- **Persistent Sessions**: Stores session configurations in JSON files for reuse across sessions.
- **Concurrent Access**: Uses file locking to ensure safe access to session configurations.
- **Logging**: Comprehensive logging for debugging and monitoring session activities.
- **Extensible**: Easily integrates with Dockerized Selenium Chrome instances and supports custom configurations.

## Installation

### Prerequisites

- Python 3.9 or higher
- Docker and Docker Compose
- Poetry (optional, for dependency management)

### Steps

#### Direct installation

Just use pip:
```bash
pip install docker-chrome-session-manager
```

Or Poetry:
```bash
poetry add docker-chrome-session-manager
```

#### Manual installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/FINWAX/docker-chrome-session-manager.py.git
   cd docker-chrome-session-manager
   ```

2. **Install dependencies**:
   Using Poetry (recommended):
   ```bash
   poetry install
   ```
   Alternatively, using pip:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Docker containers**:
   Start the Selenium Chrome containers using the provided `docker-compose.yml`:
   ```bash
   docker-compose up -d
   ```
   This will start two Selenium Chrome containers on ports `4444` and `4445`, with session data stored in the
   `./sessions` directory.

## Usage

The `docker_chrome_session_manager` module provides a `SessionManager` class to manage browser sessions. Below is an
example of how to use it:

```python
import logging
from docker_chrome_session_manager import SessionManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Initialize SessionManager with container URLs
container_paths = ["http://localhost:4444", "http://localhost:4445"]
manager = SessionManager(container_paths=container_paths)

# Create a session configuration
resource_id = "test-session-123"
config = manager.provide_session_config(
    resource_id=resource_id,
    locale="en-US",
    timezone="America/New_York",
    extra_chrome_options=["--disable-notifications"]
)

# Start a browser session
driver = manager.get_remote_driver(resource_id, config)
if driver:
    try:
        driver.get("https://example.com")
        print(f"Page title: {driver.title}")
    finally:
        driver.quit()
        manager.forget_session_config(resource_id)  # Clean up session
```

See the `example/example.py` file for a more detailed example that demonstrates multiple sessions with different
configurations.

## Configuration

The `SessionManagerConfig` dataclass provides global settings for the `SessionManager`. Key parameters include:

- `config_dir`: Directory for storing session configuration files (default: `config/sessions`).
- `session_dir`: Directory for browser session data (default: `/sessions` in Docker containers).
- `screen_resolutions`: Available screen resolutions (e.g., `(1920, 1080)`, `(1280, 720)`).
- `default_locale`: Default browser locale (e.g., `en-US`).
- `user_agent_platforms`: Platforms for generating user agents (e.g., `desktop`).
- `file_lock_timeout`: Timeout for file locking (default: 10 seconds).
- `container_response_timeout`: Timeout for container status checks (default: 3 seconds).

The `SessionConfig` dataclass allows customization of individual sessions, including:

- `user_agent`: Custom user agent string.
- `locale`: Browser locale (e.g., `en-US`, `ru-RU`).
- `resolution`: Screen resolution as a tuple (e.g., `(1920, 1080)`).
- `timezone`: Timezone ID (e.g., `America/New_York`).
- `extra_chrome_options`: Additional Chrome command-line options.

## Running the Example

To run the example script provided in `example/example.py`:

1. Ensure Docker containers are running:
   ```bash
   docker-compose -f example/docker-compose.yml up -d
   ```

2. Run the example script:
   ```bash
   poetry run python example/example.py
   ```
   or, if using pip:
   ```bash
   python example/example.py
   ```

The script will create two browser sessions with different configurations, navigate to specified URLs, and log session
details.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
