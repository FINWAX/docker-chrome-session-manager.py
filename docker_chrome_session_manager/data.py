from dataclasses import dataclass, field
from typing import Tuple, List, Optional

@dataclass
class SessionConfig:
    """
    Configuration for a browser session.

    This dataclass holds settings for a single browser session, including user agent,
    locale, resolution, timezone, and additional Chrome options.

    :param user_agent: Custom user agent string for the browser session.
    :type user_agent: Optional[str]
    :param locale: Browser locale (e.g., 'en-US').
    :type locale: Optional[str]
    :param resolution: Screen resolution as (width, height).
    :type resolution: Optional[Tuple[int, int]]
    :param timezone: Timezone ID (e.g., 'America/New_York').
    :type timezone: Optional[str]
    :param extra_chrome_options: Additional Chrome command-line options.
    :type extra_chrome_options: List[str]
    """
    user_agent: Optional[str] = None
    locale: Optional[str] = None
    resolution: Optional[Tuple[int, int]] = None
    timezone: Optional[str] = None
    extra_chrome_options: List[str] = field(default_factory=list)


@dataclass
class SessionManagerConfig:
    """
    Configuration for the SessionManager.

    This dataclass defines global settings for managing browser sessions, including
    directories, screen resolutions, timeouts, and other parameters.

    :param config_dir: Directory for storing session configuration files.
    :type config_dir: str
    :param session_dir: Directory for storing browser session data.
    :type session_dir: str
    :param screen_resolutions: List of available screen resolutions.
    :type screen_resolutions: Tuple[Tuple[int, int], ...]
    :param default_locale: Default locale for sessions (e.g., 'en-US').
    :type default_locale: str
    :param user_agent_platforms: Platforms for generating user agents (e.g., 'desktop').
    :type user_agent_platforms: Tuple[str, ...]
    :param resource_id_pattern_expression: Regex pattern for valid resource IDs.
    :type resource_id_pattern_expression: str
    :param file_lock_timeout: Timeout for file locking in seconds.
    :type file_lock_timeout: int
    :param container_response_timeout: Timeout for container status checks in seconds.
    :type container_response_timeout: int
    :param json_dump_indent: Indentation level for JSON configuration files.
    :type json_dump_indent: int
    :param container_path_choice_retries: Number of retries for choosing a container.
    :type container_path_choice_retries: int
    :param container_path_choice_retry_delay: Delay between container choice retries in seconds.
    :type container_path_choice_retry_delay: int
    """
    config_dir: str = "config/sessions"
    session_dir: str = "/sessions"
    screen_resolutions: Tuple[Tuple[int, int], ...] = (
        (1920, 1440), (1920, 1080), (1680, 1050), (1600, 1200),
        (1440, 900), (1400, 1050), (1366, 768), (1280, 720),
    )
    default_locale: str = 'en-US'
    user_agent_platforms: Tuple[str, ...] = ('desktop',)
    resource_id_pattern_expression: str = r'^[a-zA-Z0-9_-]+$'
    file_lock_timeout: int = 10
    container_response_timeout: int = 3
    json_dump_indent: int = 2
    container_path_choice_retries: int = 3
    container_path_choice_retry_delay: int = 1