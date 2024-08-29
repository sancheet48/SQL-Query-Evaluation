import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from sql_bot.lib.bot import (
    retrieve_vdb,
    model_output,
    get_api_response_template,
    sql_connect,
    get_db_query,
)


# Mocking the external dependencies
@pytest.fixture
def mock_chat_collection():
    mock_collection = MagicMock()
    mock_collection.query.return_value = {
        "documents": [["document1", "document2"]],
        "metadatas": [[{"response": "response1"}, {"response": "response2"}]],
        "distances": [[0.1, 0.2]],
    }
    return mock_collection

@pytest.fixture
def mock_llm_chain():
    mock_chain = MagicMock()
    mock_chain.run.return_value = "SELECT * FROM users;"
    return mock_chain

@pytest.fixture
def mock_output_modifier():
    with patch("sql_bot.lib.bot.output_modifier") as mock_modifier:
        mock_modifier.query_parser.return_value = "SELECT * FROM users;"
        mock_modifier.add_case_insensetiveness.return_value = "SELECT * FROM users COLLATE NOCASE"
        mock_modifier.validate_sql.return_value = True
        yield mock_modifier

# Test cases
def test_retrieve_vdb(mock_chat_collection):
    with patch("sql_bot.lib.bot.CHAT_COLLECTION", mock_chat_collection):
        examples, similarity_scores = retrieve_vdb("test query")
        assert examples == "{\n    'question': 'document1',\n    'sql_query': 'response1'\n},\n{\n    'question': 'document2',\n    'sql_query': 'response2'\n}"
        assert similarity_scores == [0.9, 0.8]

def test_retrieve_vdb_no_collection():
    with patch("sql_bot.lib.bot.CHAT_COLLECTION", None):
        examples, similarity_scores = retrieve_vdb("test query")
        assert examples == ""
        assert similarity_scores == []

def test_model_output(mock_llm_chain):
    with patch("sql_bot.lib.bot.LLM_CHAIN", mock_llm_chain), \
         patch("sql_bot.lib.bot.LLM_SCHEMA", "test schema"), \
         patch("sql_bot.lib.bot.time") as mock_time:
        mock_time.side_effect = [1, 2]  # Simulate time passing
        api_response = model_output("test question", "test examples", [0.5, 0.6])
        assert api_response == {
            "model_response": "SELECT * FROM users;",
            "is_valid_syntax": False,
            "time_taken": 1,
            "examples": "test examples",
            "similarity_scores": [0.5, 0.6],
        }

def test_get_api_response_template():
    api_response = get_api_response_template()
    assert api_response == {
        "model_response": "",
        "is_valid_syntax": False,
        "time_taken": 0,
        "examples": "",
        "similarity_scores": [],
    }

def test_sql_connect(mock_output_modifier):
    api_response = {"model_response": "SELECT * FROM users;"}
    result = sql_connect(api_response)
    assert result["model_response"] == "SELECT * FROM users COLLATE NOCASE"
    assert result["is_valid_syntax"] is True

def test_get_db_query(mock_chat_collection, mock_llm_chain, mock_output_modifier):
    with patch("sql_bot.lib.bot.CHAT_COLLECTION", mock_chat_collection), \
         patch("sql_bot.lib.bot.LLM_CHAIN", mock_llm_chain), \
         patch("sql_bot.lib.bot.time") as mock_time:
        mock_time.side_effect = [1, 2]
        app = TestClient(get_db_query)
        response = app.get("/", params={"query": "test query"})
        assert response.status_code == 200
        assert response.json() == {
            "model_response": "SELECT * FROM users COLLATE NOCASE",
            "is_valid_syntax": True,
            "time_taken": 1,
            "examples": "{\n    'question': 'document1',\n    'sql_query': 'response1'\n},\n{\n    'question': 'document2',\n    'sql_query': 'response2'\n}",
            "similarity_scores": [0.9, 0.8],
        }

