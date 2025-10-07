import logging
from datetime import datetime
import anvil.server


class SessionContextFilter(logging.Filter):
    def __init__(self, session_store):
        super().__init__()
        self.session_store = session_store

    def filter(self, record):
        try:
            session_id = anvil.server.get_session_id()
            user_email = self.session_store.get(session_id, {}).get("user_email", "Unknown user")
        except Exception:
            session_id = "unknown"
            user_email = "unknown"

        record.session_id = session_id
        record.user_email = user_email
        return True


class SessionLogger:
    def __init__(self, session_store):
        self.session_store = session_store
        self.logger = logging.getLogger("SessionLogger")
        self.logger.setLevel(logging.INFO)

        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter("[%(asctime)s][%(user_email)s][%(session_id)s] %(message)s")
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        # Add the dynamic filter
        self.logger.addFilter(SessionContextFilter(self.session_store))

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)

