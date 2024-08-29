"""Constants defined module."""
import os


PROJECT_DIR = os.path.dirname(os.path.realpath(__file__))


LLM_SCHEMA_PATH = os.path.join(PROJECT_DIR, "sql_bot/lib", "llm_schema.txt")
GPU_LAYERS = int(os.environ.get("GPU_LAYERS", 0))
CHROMA_DB_PATH = os.environ.get("CHROMA_DB_PATH", "")


SERVICE_COM_TOKEN = os.environ.get("SERVICE_COM_TOKEN", "")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

SQL_DB_PATH = os.environ.get("SQL_DB_PATH", r"D:\Downloads\train\train\train_databases\train_databases\cars\cars.sqlite")
