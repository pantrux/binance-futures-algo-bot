from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from apps.api.app.core.settings import settings


engine = create_engine(settings.postgres_dsn, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
