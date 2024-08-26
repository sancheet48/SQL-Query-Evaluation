"""Constants defined module."""
import os


PROJECT_DIR = os.path.dirname(os.path.realpath(__file__))


LLM_SCHEMA_PATH = os.path.join(PROJECT_DIR, "lib", "llm_schema3.txt")
GPU_LAYERS = int(os.environ.get("GPU_LAYERS", 0))
CHROMA_DB_PATH = os.environ.get("CHROMA_DB_PATH", "")


SERVICE_COM_TOKEN = os.environ.get("SERVICE_COM_TOKEN", "")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
