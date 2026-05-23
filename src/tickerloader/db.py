import logging
import os
from contextlib import contextmanager

import boto3
import psycopg2
from psycopg2 import pool

logger = logging.getLogger()
logger.setLevel(logging.INFO)

_pool: pool.ThreadedConnectionPool | None = None

# DB_AUTH_MODE controls how the app authenticates with RDS.
#   iam      - Uses a short-lived IAM auth token generated from the ECS task role.
#              Requires DB_USERNAME to be an rds_iam-enabled Postgres user.
#              Requires AWS_REGION to be set. DB_PASSWORD is ignored.
#   password - Uses DB_USERNAME and DB_PASSWORD directly.
#              Falls back to this mode if DB_AUTH_MODE is not set.
_AUTH_MODE_IAM = "iam"
_AUTH_MODE_PASSWORD = "password"


def _get_auth_mode() -> str:
    mode = os.environ.get("DB_AUTH_MODE", _AUTH_MODE_PASSWORD).lower()
    if mode not in (_AUTH_MODE_IAM, _AUTH_MODE_PASSWORD):
        raise ValueError(f"Invalid DB_AUTH_MODE '{mode}'. Must be 'iam' or 'password'.")
    return mode


def _get_iam_auth_token() -> str:
    rds_client = boto3.client("rds", region_name=os.environ["AWS_REGION"])
    return rds_client.generate_db_auth_token(
        DBHostname=os.environ["DB_HOST"],
        Port=int(os.environ.get("DB_PORT", "5432")),
        DBUsername=os.environ["DB_USERNAME"],
    )


def _get_password() -> str:
    return os.environ["DB_PASSWORD"]


def _create_pool() -> pool.ThreadedConnectionPool:
    auth_mode = _get_auth_mode()
    if auth_mode == _AUTH_MODE_IAM:
        logger.info("Creating database connection pool using IAM auth")
        password = _get_iam_auth_token()
        sslmode = "verify-full"  # Required for IAM auth
    else:
        logger.info("Creating database connection pool using password auth")
        password = _get_password()
        sslmode = os.environ.get("DB_SSLMODE", "require")

    return pool.ThreadedConnectionPool(
        minconn=1,
        maxconn=int(os.environ.get("DB_POOL_MAX_CONN", "5")),
        host=os.environ["DB_HOST"],
        port=int(os.environ.get("DB_PORT", "5432")),
        database=os.environ["DB_NAME"],
        user=os.environ["DB_USERNAME"],
        password=password,
        sslmode=sslmode,
    )


def get_pool() -> pool.ThreadedConnectionPool:
    """Returns the module-level pool, creating it on first call."""
    global _pool
    if _pool is None or _pool.closed:
        _pool = _create_pool()
    return _pool


@contextmanager
def get_connection():
    """
    Context manager that checks out a connection from the pool and returns
    it when the block exits.

    In IAM auth mode, handles token expiry by refreshing the pool and
    retrying once on OperationalError. In password mode, the error is
    raised immediately without a retry since credentials don't expire.

    Usage:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(...)
    """
    connection = None
    try:
        connection = get_pool().getconn()
        yield connection
        connection.commit()
    except psycopg2.OperationalError as e:
        if connection is not None:
            try:
                get_pool().putconn(connection, close=True)
            except Exception as exc:
                logger.warning("Failed to return connection to pool: %s", exc)
            connection = None

        if _get_auth_mode() == _AUTH_MODE_IAM:
            # IAM tokens expire after 15 minutes — recreate the pool with a
            # fresh token and retry once.
            logger.warning("DB connection failed, refreshing IAM token and retrying: %s", e)
            global _pool
            _pool = _create_pool()
            connection = _pool.getconn()
            try:
                yield connection
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        else:
            raise
    except Exception:
        if connection is not None:
            connection.rollback()
        raise
    finally:
        if connection is not None:
            get_pool().putconn(connection)
