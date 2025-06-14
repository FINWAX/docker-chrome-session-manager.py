import os
import json
import random
import re
import logging
import time
from dataclasses import asdict
import requests
from filelock import FileLock
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.webdriver import WebDriver
from typing import List, Optional

from docker_chrome_session_manager.data import SessionManagerConfig, SessionConfig

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Manages Selenium Chrome sessions across multiple Docker containers.

    This class provides methods to create, configure, and manage browser sessions,
    including selecting free containers, setting user agents, locales, resolutions,
    timezones, and additional Chrome options.
    """

    def __init__(self, container_paths: Optional[List[str]] = None, config: None | SessionManagerConfig = None):
        """
        Initialize the SessionManager.
        :param container_paths: List of URLs for Selenium container endpoints.
        :type container_paths: Optional[List[str]]
        :param config: Configuration for session management.
        :type config: Optional[SessionManagerConfig]
        """
        self.config = config or SessionManagerConfig()
        self.container_paths = [path.rstrip('/') for path in (container_paths or [])]
        self.user_agent_factory = UserAgent(platforms=self.config.user_agent_platforms)
        os.makedirs(self.config.config_dir, exist_ok=True)
        self.resource_id_pattern = re.compile(self.config.resource_id_pattern_expression)
        logger.info(
            f"SessionManager initialized with config_dir: {self.config.config_dir}, "
            f"session_dir: {self.config.session_dir}, containers: {self.container_paths}."
        )

    def get_remote_driver(self, resource_id: str, session_config: Optional[SessionConfig] = None) -> None | WebDriver:
        """
        Create or retrieve a WebDriver instance for a session.
        :param resource_id: Unique identifier for the session.
        :type resource_id: str
        :param session_config: Session configuration, if provided.
        :type session_config: Optional[SessionConfig]
        :return: WebDriver instance or None if creation fails.
        :rtype: Optional[WebDriver]
        :raises ValueError: If resource_id is invalid.
        """
        resource_id = str(resource_id)
        if self._invalid_resource_id(resource_id):
            logger.error(f"Invalid resource ID: {resource_id}")
            return None

        if not session_config:
            loaded_config = self._load_session_config_fields(resource_id)
            if not loaded_config:
                logger.warning(f"No session configuration found for resource_id: {resource_id}.")
                return None
            session_config = SessionConfig(**loaded_config)
            logger.info(f"Loaded existing session configuration for resource_id: {resource_id}.")

        container_path = self._choose_free_container_path()
        if not container_path:
            logger.error("No free containers available.")
            return None

        options = Options()
        options.add_argument(f"--user-agent={session_config.user_agent}")
        options.add_argument(f"--window-size={session_config.resolution[0]},{session_config.resolution[1]}")
        options.add_argument(f"--lang={session_config.locale}")
        if session_config.timezone:
            options.add_argument(f"--tz={session_config.timezone}")
            logger.debug(f"Added timezone argument: {session_config.timezone}.")
        for opt in session_config.extra_chrome_options:
            options.add_argument(opt)
        options.add_argument(f"--user-data-dir={self.config.session_dir}/{resource_id}")
        logger.debug(f"Chrome options configured for resource_id: {resource_id}.")

        try:
            driver = webdriver.Remote(
                command_executor=f"{container_path}/wd/hub",
                options=options
            )
            # Set timezone via CDP if specified
            if session_config.timezone:
                driver.execute_cdp_cmd("Emulation.setTimezoneOverride", {"timezoneId": session_config.timezone})
                logger.debug(f"Set timezone via CDP to: {session_config.timezone}.")
            logger.info(f"WebDriver created for resource_id: {resource_id} on container: {container_path}.")
            return driver
        except Exception as e:
            logger.error(f"Failed to create WebDriver for resource_id: {resource_id} "
                          f"on container {container_path}: {str(e)}.")
            return None

    def forget_session_config(self, resource_id: str) -> bool:
        """
        Delete the session configuration for a resource.
        :param resource_id: Unique identifier for the session.
        :type resource_id: str
        :return: True if configuration was deleted, False otherwise.
        :rtype: bool
        :raises ValueError: If resource_id is invalid.
        """
        resource_id = str(resource_id)
        if self._invalid_resource_id(resource_id):
            logger.error(f"Invalid resource ID for forgetting session: {resource_id}.")
            return False
        config_path = self._get_session_config_path(resource_id)
        if os.path.exists(config_path):
            os.remove(config_path)
            logger.info(f"Session configuration deleted for resource_id: {resource_id}.")
            return True
        logger.warning(f"No session configuration found to delete for resource_id: {resource_id}.")
        return False

    def provide_session_config(
        self,
        resource_id: str,
        locale: Optional[str] = None,
        timezone: Optional[str] = None,
        extra_chrome_options: Optional[List[str]] = None
    ) -> SessionConfig:
        """
        Provide a session configuration for the specified resource_id.
        :param resource_id: Unique identifier for the session.
        :type resource_id: str
        :param locale: Browser locale (e.g., 'en-US').
        :type locale: Optional[str]
        :param timezone: Timezone ID (e.g., 'America/New_York').
        :type timezone: Optional[str]
        :param extra_chrome_options: Additional Chrome command-line options.
        :type extra_chrome_options: Optional[List[str]]
        :return: Session configuration object.
        :rtype: SessionConfig
        :raises ValueError: If resource_id is invalid.
        """
        resource_id = str(resource_id)
        if self._invalid_resource_id(resource_id):
            logger.error(f"Invalid resource ID for providing session config: {resource_id}.")
            raise ValueError("Invalid resource ID.")

        loaded_config_fields = self._load_session_config_fields(resource_id)
        if loaded_config_fields:
            session_config = SessionConfig(**loaded_config_fields)
            logger.info(f"Loaded existing session configuration for resource_id: {resource_id}.")
        else:
            session_config = SessionConfig()
            logger.info(f"Created new session configuration for resource_id: {resource_id}.")

        if not session_config.user_agent:
            session_config.user_agent = self.user_agent_factory.random
            logger.debug(f"Generated random user agent: {session_config.user_agent}.")

        if not session_config.resolution:
            session_config.resolution = random.choice(self.config.screen_resolutions)
            logger.debug(f"Selected random resolution: {session_config.resolution}.")

        if not session_config.locale:
            session_config.locale = self.config.default_locale
            logger.debug(f"Set default locale: {session_config.locale}.")

        if locale:
            session_config.locale = locale
            logger.debug(f"Updated locale to: {locale}.")

        if timezone:
            session_config.timezone = timezone
            logger.debug(f"Updated timezone to: {timezone}.")

        if extra_chrome_options:
            session_config.extra_chrome_options = extra_chrome_options
            logger.debug(f"Updated extra Chrome options: {extra_chrome_options}.")

        session_config_fields = asdict(session_config)
        if session_config_fields != loaded_config_fields:
            self._save_session_config(resource_id, session_config_fields)
            logger.info(f"Saved updated session configuration for resource_id: {resource_id}.")

        return session_config

    def _choose_free_container_path(self) -> Optional[str]:
        """
        Select a free container by checking its status via /status endpoint.
        :return: URL of the free container (e.g., 'http://localhost:4444') or None if none available.
        :rtype: Optional[str]
        """
        if not self.container_paths:
            logger.warning("Containers are not defined.")
            return None
        for attempt in range(self.config.container_path_choice_retries):
            for container_path in self.container_paths:
                e = None
                try:
                    url = f"{container_path}/wd/hub/status"
                    response = requests.get(url, timeout=self.config.container_response_timeout)
                    if response.status_code == requests.codes.ok and response.json().get('value', {}).get('ready', False):
                        logger.debug(f"Container available: {container_path} on attempt {attempt + 1}.")
                        return container_path
                except Exception as e:
                    pass
                logging.log(
                    logging.WARNING if e else logging.INFO,
                    f"Container unavailable: {container_path} on attempt {attempt + 1}, error: {str(e)}."
                )
            logger.debug(
                f"No free containers found on attempt {attempt + 1}, "
                f"retrying after {self.config.container_path_choice_retry_delay}s."
            )
            time.sleep(self.config.container_path_choice_retry_delay)

        logger.warning("No free containers found after all retries.")
        return None

    def _get_session_config_path(self, resource_id: str) -> str:
        """
        Get the file path for a session configuration.
        :param resource_id: Unique identifier for the session.
        :type resource_id: str
        :return: File path for the configuration.
        :rtype: str
        :raises ValueError: If resource_id is invalid.
        """
        resource_id = str(resource_id)
        if self._invalid_resource_id(resource_id):
            logger.error(f"Invalid resource ID for config path: {resource_id}.")
            raise ValueError("Invalid resource ID.")
        return os.path.join(self.config.config_dir, f"{resource_id}.json")

    def _load_session_config_fields(self, resource_id: str) -> Optional[dict]:
        """
        Load session configuration fields from a file.
        :param resource_id: Unique identifier for the session.
        :type resource_id: str
        :return: Configuration fields as a dictionary or None if not found.
        :rtype: Optional[dict]
        """
        config_path = self._get_session_config_path(resource_id)
        lock_path = config_path + ".lock"
        with FileLock(lock_path, timeout=self.config.file_lock_timeout):
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    logger.debug(f"Loading session configuration from: {config_path}.")
                    return json.load(f)
        logger.debug(f"No session configuration found at: {config_path}.")
        return None

    def _save_session_config(self, resource_id: str, config: dict):
        """
        Save session configuration to a file.
        :param resource_id: Unique identifier for the session.
        :type resource_id: str
        :param config: Configuration fields to save.
        :type config: dict
        """
        config_path = self._get_session_config_path(resource_id)
        lock_path = config_path + ".lock"
        with FileLock(lock_path, timeout=self.config.file_lock_timeout):
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=self.config.json_dump_indent)
            logger.debug(f"Saved session configuration to: {config_path}.")

    def _invalid_resource_id(self, resource_id: str) -> bool:
        """
        Check if a resource ID is invalid based on the pattern.
        :param resource_id: Unique identifier to validate.
        :type resource_id: str
        :return: True if the ID is invalid, False otherwise.
        :rtype: bool
        """
        return not bool(re.match(self.resource_id_pattern, resource_id))
