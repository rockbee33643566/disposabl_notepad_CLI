import asyncio
import os
from pathlib import Path

from aiologger import Logger
from aiologger.formatters.base import Formatter
from aiologger.handlers.files import BaseAsyncRotatingFileHandler
from aiologger.levels import LogLevel
from aiologger.records import LogRecord

MAX_LOG_SIZE = 1024 * 1024
LOG_FORMAT = "%(asctime)s %(levelname)-8s %(name)s: %(message)s"


def _log_path() -> Path:
    return Path(__file__).parent.parent / "data" / "client.log"


class AsyncSizeRotatingFileHandler(BaseAsyncRotatingFileHandler):
    def __init__(
        self,
        filename: str,
        max_bytes: int = MAX_LOG_SIZE,
        backup_count: int = 1,
        encoding: str = "utf-8",
    ) -> None:
        super().__init__(filename=filename, mode="a", encoding=encoding)
        self.max_bytes = max_bytes
        self.backup_count = backup_count

    def should_rollover(self, record: LogRecord) -> bool:
        if not os.path.exists(self.absolute_file_path):
            return False

        current_size = os.path.getsize(self.absolute_file_path)
        record_size = len(self.formatter.format(record)) + len(self.terminator)
        return current_size + record_size > self.max_bytes

    async def do_rollover(self) -> None:
        if self.stream:
            await self.stream.close()
            self.stream = None

        loop = asyncio.get_running_loop()

        if self.backup_count > 0:
            for index in range(self.backup_count - 1, 0, -1):
                source = f"{self.absolute_file_path}.{index}"
                destination = f"{self.absolute_file_path}.{index + 1}"
                if await loop.run_in_executor(None, os.path.exists, source):
                    await loop.run_in_executor(None, os.replace, source, destination)

            backup = f"{self.absolute_file_path}.1"
            if await loop.run_in_executor(None, os.path.exists, backup):
                await loop.run_in_executor(None, os.remove, backup)
            await self.rotate(self.absolute_file_path, backup)
        else:
            await loop.run_in_executor(None, os.remove, self.absolute_file_path)

        await self._init_writer()


_logger: Logger | None = None


def get_logger() -> Logger:
    global _logger

    if _logger is not None:
        return _logger

    path = _log_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    handler = AsyncSizeRotatingFileHandler(str(path), max_bytes=MAX_LOG_SIZE)
    handler.formatter = Formatter(LOG_FORMAT)
    handler.level = LogLevel.INFO

    logger = Logger(name="client", level=LogLevel.DEBUG)
    logger.add_handler(handler)

    _logger = logger
    return _logger
