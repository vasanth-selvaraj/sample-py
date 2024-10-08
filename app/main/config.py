import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "supersecretkey"
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres:root@localhost/mdx"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"connect_args": {"options": "-csearch_path=mercury"}}
    SECRET_KEY = os.environ.get("SECRET_KEY") or "your_secret_key"
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY") or "mkcod8u30ijosknvdu"
    LOGS_PATH = os.getenv("LOGS_PATH", "./logs")
    DEBUG = False


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(
        basedir, "flask_boilerplate_main.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    @staticmethod
    def get_db_connection():
        import psycopg2

        conn = psycopg2.connect(
            host="localhost",
            database="mdx2.0",
            user="postgres",
            password="root",
            options=f"-c search_path=public",
        )
        return conn


class TestingConfig(Config):
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(
        basedir, "flask_boilerplate_test.db"
    )
    PRESERVE_CONTEXT_ON_EXCEPTION = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    @staticmethod
    def get_db_connection():
        import psycopg2

        conn = psycopg2.connect(
            host="localhost",
            database="mdx2.0",
            user="postgres",
            password="root",
            options=f"-c search_path=public",
        )
        return conn


class ProductionConfig(Config):
    DEBUG = False


config_by_name = dict(dev=DevelopmentConfig, test=TestingConfig, prod=ProductionConfig)

key = Config.SECRET_KEY
