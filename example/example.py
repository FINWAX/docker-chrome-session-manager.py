import logging
import random
from time import sleep

from docker_chrome_session_manager import SessionManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


def run_browser_session(resource_id, url, locale, timezone, container_paths, wait_secs=5):
    # Initialize SessionManager
    manager = SessionManager(container_paths=container_paths)

    # Provide session configuration with custom locale and extra options
    config = manager.provide_session_config(
        resource_id=resource_id,
        locale=locale,
        timezone=timezone,
        extra_chrome_options=["--disable-notifications"]
    )

    driver = None
    try:
        # Get browser instance
        driver = manager.get_remote_driver(resource_id, config)
        if not driver:
            logging.error(f"Failed to create browser for resource_id: {resource_id}")
            return

        driver.get(url)

        logging.info(f'Sleep {wait_secs} for resource: {resource_id}')
        sleep(wait_secs)

        title = driver.title
        user_agent = driver.execute_script("return navigator.userAgent;")
        languages = driver.execute_script("return navigator.languages;")
        window_size = driver.get_window_size()
        timezone_IANA = driver.execute_script("return Intl.DateTimeFormat().resolvedOptions().timeZone;")
        timezone_datetime = driver.execute_script("return (new Date()).toTimeString().slice(9);")

        # Print session details
        logging.info(f'Resource ID: {resource_id}')
        logging.info(f'URL: {url}')
        logging.info(f'Page Title: {title}')
        logging.info(f'User-Agent: {user_agent}')
        logging.info(f'Languages: {languages}')
        logging.info(f'Window Size: Driver[{window_size}] vs Config[{config.resolution}]')
        logging.info(
            f'Timezone: DriverIANA[{timezone_IANA}], DriverDatetime[{timezone_datetime}] vs Config[{config.timezone}]'
        )

    except Exception as e:
        logging.error(f"Error in session for resource_id {resource_id}: {str(e)}")
    finally:
        if driver:
            driver.quit()
        manager.forget_session_config(resource_id)


def main():
    container_paths = [
        "http://localhost:4444",
        "http://localhost:4445"
    ]

    sessions = [
        {
            "resource_id": f"test-{random.randint(1, 1000)}",
            "url": "https://google.com", "locale": "en-US", 'timezone': 'America/Denver',
            "wait_secs": 3
        },
        {
            "resource_id": f"test-{random.randint(1, 1000)}",
            "url": "https://bing.com", "locale": "ru-RU", 'timezone': 'Europe/Minsk',
            "wait_secs": 3
        }
    ]

    for session in sessions:
        run_browser_session(
            session['resource_id'], session['url'], session['locale'], session['timezone'],
            container_paths, session['wait_secs']
        )


if __name__ == "__main__":
    main()
