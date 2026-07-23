import json
import logging
import time
from datetime import datetime

class StructuredJSONFormatter(logging.Formatter):
    """
    Structured JSON log formatter for production.
    """
    def format(self, record):
        log_record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Include exception traceback if present
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        
        # Include custom attributes from log call extra={}
        for key, val in record.__dict__.items():
            if key not in ["args", "asctime", "created", "exc_info", "exc_text", "filename",
                           "funcName", "levelname", "levelno", "lineno", "module", "msecs",
                           "msg", "name", "pathname", "process", "processName", "relativeCreated",
                           "stack_info", "thread", "threadName"]:
                log_record[key] = val
        
        return json.dumps(log_record)

class EduOrbitLogger:
    """
    Enterprise Structured Logger providing partitioned logging namespaces.
    """
    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        return logging.getLogger(f"eduorbit.{name}")

    @classmethod
    def security(cls, msg: str, tenant_id=None, user_id=None, **kwargs):
        cls.get_logger("security").warning(
            msg, extra={"tenant_id": str(tenant_id) if tenant_id else None, 
                        "user_id": str(user_id) if user_id else None, **kwargs}
        )

    @classmethod
    def audit(cls, msg: str, tenant_id=None, user_id=None, action=None, resource=None, **kwargs):
        cls.get_logger("audit").info(
            msg, extra={
                "tenant_id": str(tenant_id) if tenant_id else None,
                "user_id": str(user_id) if user_id else None,
                "action": action,
                "resource": resource,
                **kwargs
            }
        )

    @classmethod
    def api(cls, msg: str, method=None, path=None, status_code=None, duration=None, **kwargs):
        cls.get_logger("api").info(
            msg, extra={
                "method": method,
                "path": path,
                "status_code": status_code,
                "duration_ms": duration,
                **kwargs
            }
        )

    @classmethod
    def payment(cls, msg: str, tenant_id=None, amount=None, transaction_id=None, status=None, **kwargs):
        cls.get_logger("payment").info(
            msg, extra={
                "tenant_id": str(tenant_id) if tenant_id else None,
                "amount": str(amount) if amount else None,
                "transaction_id": transaction_id,
                "status": status,
                **kwargs
            }
        )

    @classmethod
    def ai(cls, msg: str, tenant_id=None, provider=None, tokens=None, **kwargs):
        cls.get_logger("ai").info(
            msg, extra={
                "tenant_id": str(tenant_id) if tenant_id else None,
                "provider": provider,
                "tokens_used": tokens,
                **kwargs
            }
        )
