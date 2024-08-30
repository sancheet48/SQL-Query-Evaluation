import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from unittest.mock import Mock, patch
from sql_bot.lib.bot import QueryBot
import const
from fastapi.responses import JSONResponse



@pytest.fixture
def query_bot():
    return QueryBot()


def test_startup_no_schema_file(query_bot):
    with patch('os.path.isfile', return_value=False), \
         patch('sys.exit') as mock_exit, \
         patch('logging.Logger.error') as mock_logger_error:

        query_bot.startup()

        mock_logger_error.assert_called_once_with(f"'{const.LLM_SCHEMA_PATH}' file not found")
        mock_exit.assert_called_once_with(-1)


def test_retrieve_vdb_no_collection(query_bot):
    query_bot.chat_collection = None
    result = query_bot.retrieve_vdb("sample query")
    assert result == ("", [])


def test_retrieve_vdb_with_collection(query_bot):
    mock_collection = Mock()
    query_bot.chat_collection = mock_collection
    mock_collection.query.return_value = {
        "documents": [["doc1", "doc2"]],
        "metadatas": [[{"response": "response1"}, {"response": "response2"}]],
        "distances": [[0.1, 0.2]]
    }
    
    output_string, similarity_scores = query_bot.retrieve_vdb("sample query")
    
    expected_output_string = (
        "{\n    'question': 'doc1',\n    'sql_query': 'response1'\n},\n"
        "{\n    'question': 'doc2',\n    'sql_query': 'response2'\n}"
    )
    expected_similarity_scores = [0.9, 0.8]
    
    assert output_string == expected_output_string
    assert similarity_scores == expected_similarity_scores


def test_model_output(query_bot):
    mock_llm_chain = Mock()
    query_bot.llm_chain = mock_llm_chain
    mock_llm_chain.run.return_value = "SELECT AVG(T2.price) FROM data AS T1 INNER JOIN price AS T2 ON T1.ID = T2.ID WHERE T1.model = 70"
    
    response = query_bot.model_output("What is the average price of model 70 cars?", "sample examples", [0.44424616782484705,
            0.4440249728681688,
            0.4438854719816604,
            0.42174848741233506])
    
    assert response["model_response"] == "SELECT AVG(T2.price) FROM data AS T1 INNER JOIN price AS T2 ON T1.ID = T2.ID WHERE T1.model = 70"
    assert "time_taken" in response
    assert response["similarity_scores"] == [0.44424616782484705,
            0.4440249728681688,
            0.4438854719816604,
            0.42174848741233506]


def test_get_db_query_success(query_bot):
    with patch.object(query_bot, 'retrieve_vdb', return_value=("examples", [0.9])), \
         patch.object(query_bot, 'model_output', return_value={"model_response": "SELECT AVG(T2.price) FROM data AS T1 INNER JOIN price AS T2 ON T1.ID = T2.ID WHERE T1.model = 70", "is_valid_syntax": True}), \
         patch.object(query_bot, 'sql_connect', return_value={"model_response": "SELECT AVG(T2.price) FROM data AS T1 INNER JOIN price AS T2 ON T1.ID = T2.ID WHERE T1.model = 70", "is_valid_syntax": True, "examples": "examples"}):
        
        response = query_bot.get_db_query("What is the average price of model 70 cars?")
        assert isinstance(response, JSONResponse)
        assert response.status_code == 200


def test_get_db_query_failure(query_bot):
    with patch.object(query_bot, 'retrieve_vdb', return_value=("examples", [0.9])), \
         patch.object(query_bot, 'model_output', return_value={"model_response": "SELECT AVG(T2.price) FROM data AS T1 INNER JOIN price AS T2 ON T1.ID = T2.ID WHERE T1.model = 70", "is_valid_syntax": True}), \
         patch.object(query_bot, 'sql_connect', side_effect=Exception("Test Exception")):
        
        response = query_bot.get_db_query("What is the average price of model 70 cars?")
        assert isinstance(response, JSONResponse)
        assert response.status_code == 400