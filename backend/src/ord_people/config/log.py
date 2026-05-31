from typing import final

from pydantic import BaseModel, computed_field

from ord_people.config.fields import LogLevel


@final
class LoggingConfig(BaseModel):
    format: str = "[%(asctime)s.%(msecs)03d] %(name)s:%(lineno)-3d %(levelname)-7s [req=%(request_id)s user=%(user_id)s] - %(message)s"
    level: LogLevel = "INFO"
    db_level: LogLevel = "WARNING"
    json_logs: bool = False
    access_log: bool = True
    to_file: bool = False
    file_path: str = "/var/log/ord-people/backend.log"
    file_max_size_mb: int = 10
    file_backup_count: int = 5
    slow_request_ms: int = 1000

    @computed_field()
    @property
    def max_size_bytes(self) -> int:
        return self.file_max_size_mb * 1024 * 1024
