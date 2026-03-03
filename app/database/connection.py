from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker

url = URL.create(
    drivername="postgresql+psycopg2",
    username="postgres",
    password="1vRb0NL51NMZHQagZc9ORnu19A2J0hoWW9GA3aCNjcjjatgNrgpQgca8obrPzavv",
    host="localhost",
    port=3000,
    database="postgres",
)

engine = create_engine(
    url,
    connect_args={"sslmode": "require"},
    pool_pre_ping=True
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)