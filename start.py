import asyncio
import uvicorn
from src.jobagent.main import app
from src.jobagent.config.logging import configure_logging
from src.jobagent.config.settings import settings


def main():
    configure_logging(settings.LOG_LEVEL)
    
    uvicorn.run(
        "src.jobagent.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.LOG_LEVEL.lower(),
    )


if __name__ == "__main__":
    main()
