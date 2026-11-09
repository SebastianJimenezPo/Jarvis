import json
import logging
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler


class JsonFormatter(logging.Formatter):
    def format(self, record):
        data = {"time": datetime.now(timezone.utc).isoformat(), "level": record.levelname,
                "event": record.getMessage()}
        if hasattr(record, "fields"):
            data.update(record.fields)
        if record.exc_info:
            data["exception"] = self.formatException(record.exc_info)
        return json.dumps(data, ensure_ascii=False)


def configure(root, level="INFO", debug=False):
    directory = root / "logs"
    directory.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("jarvis")
    logger.setLevel(level)
    handler = RotatingFileHandler(directory / "jarvis.jsonl", maxBytes=2_000_000, backupCount=3, encoding="utf-8")
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    if debug:
        console = logging.StreamHandler()
        console.setFormatter(JsonFormatter())
        logger.addHandler(console)
    return logger
