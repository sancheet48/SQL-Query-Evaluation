import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import sqlite3

from unittest.mock import patch, Mock
import pytest
import requests
import requests_mock
from sql_bot.metrics.validation import (
    connect_to_database,
    execute_query,
    send_question_to_llm,
    evaluate_answers,
    SQL_DB_PATH,
    output_data,
    correct_output_data,
    incorrect_output_data,

)

@pytest.fixture
def mock_connection():
    return Mock(spec=sqlite3.Connection)

@pytest.fixture
def mock_cursor():
    return Mock(spec=sqlite3.Cursor)

def test_connect_to_database():
    with patch("sqlite3.connect") as mock_connect:
        mock_connect.return_value = Mock(spec=sqlite3.Connection)
        connection = connect_to_database()
        mock_connect.assert_called_once_with(SQL_DB_PATH)
        assert isinstance(connection, sqlite3.Connection)


def test_execute_query(mock_connection, mock_cursor):
    mock_connection.cursor.return_value = mock_cursor
    mock_cursor.fetchall.return_value = [20000.0]

    query = "SELECT T2.price FROM data AS T1 INNER JOIN price AS T2 ON T1.ID = T2.ID WHERE T1.car_name = 'peugeot 505s turbo diesel"
    result = execute_query(mock_connection, query)

    assert result == [20000.0]


@pytest.fixture
def mock_response_data():
    return {
        "model_response": "SELECT T3.country FROM data AS T1 INNER JOIN production AS T2 ON T1.ID = T2.ID INNER JOIN country AS T3 ON T2.country = T3.origin WHERE T1.car_name = 'ford torino' AND T2.model_year = 1970 COLLATE NOCASE ",
        "is_valid_syntax": True,
        "time_taken": 7.874291896820068,
        "examples": "sample exmples",
        "similarity_scores": [
            0.3227739172667008,
            0.24021300012215674,
            0.2238425084092438,
            0.22098778594514024
        ]
    }

def test_send_question_to_llm_success(requests_mock, mock_response_data):
    # Arrange
    question = "What was the origin country of the car model ford torino produced in 1970"
    url = "http://localhost:8000/api/v1/bot/query"
    requests_mock.post(url, json=mock_response_data, status_code=200)

    # Act
    response = send_question_to_llm(question)

    # Assert
    assert response == mock_response_data


def test_send_question_to_llm_failure(requests_mock, capsys):
    # Arrange
    question = "What was the origin country of the car model ford torino produced in 1970"
    url = "http://localhost:8000/api/v1/bot/query"
    requests_mock.post(url, status_code=404)

    # Act
    response = send_question_to_llm(question)

    # Assert
    assert response is None
    captured = capsys.readouterr()
    assert "Error: 404" in captured.out

@pytest.fixture
def sample_llm_answer_dict():
    return {
        "model_response": "SELECT T2.price FROM data AS T1 INNER JOIN price AS T2 ON T1.ID = T2.ID WHERE T1.car_name = 'Peugeot 504 (sw)' COLLATE NOCASE ",
        "is_valid_syntax": True,
        "examples": "examples ",
        "similarity_scores": [
            0.2779632783921244,
            0.1970904087211579,
            0.18394168173651493,
            0.15472299696022218
        ]
    }

@pytest.fixture
def setup_and_teardown():
    # Clear the global lists before each test
    output_data.clear()
    correct_output_data.clear()
    incorrect_output_data.clear()
    yield
    # Clear the global lists after each test
    output_data.clear()
    correct_output_data.clear()
    incorrect_output_data.clear()

@pytest.mark.usefixtures("setup_and_teardown")
class TestEvaluateAnswers:

    def test_incorrect_answer(self, mock_connection, sample_llm_answer_dict):
        with patch('sql_bot.metrics.validation.execute_query') as mock_execute_query:
            mock_execute_query.side_effect = [[[16035.29706]], [[20000.0]]]
            
            question = "How much is the Peugeot 505s Turbo Diesel?"
            correct_answer = "SELECT T2.price FROM data AS T1 INNER JOIN price AS T2 ON T1.ID = T2.ID WHERE T1.car_name = 'peugeot 505s turbo diesel'"
            
            result = evaluate_answers(question, sample_llm_answer_dict, correct_answer, mock_connection)

            assert result == False
            assert len(output_data) == 1
            assert len(correct_output_data) == 0
            assert len(incorrect_output_data) == 1
            
            assert output_data[0]['question'] == question
            assert output_data[0]['llm_answer'] == sample_llm_answer_dict['model_response']
            assert output_data[0]['llm_results'] == [[16035.29706]]
            assert output_data[0]['correct_answer'] == correct_answer
            assert output_data[0]['correct_results'] == [[20000.0]]
            assert output_data[0]['examples'] == "examples "
            assert output_data[0]['similarity_scores'] == sample_llm_answer_dict['similarity_scores']

    def test_correct_answer(self, mock_connection, sample_llm_answer_dict):
        with patch('sql_bot.metrics.validation.execute_query') as mock_execute_query:
            mock_execute_query.return_value = [[20000.0]]
            
            question = "How much is the Peugeot 505s Turbo Diesel?"
            correct_answer = "SELECT T2.price FROM data AS T1 INNER JOIN price AS T2 ON T1.ID = T2.ID WHERE T1.car_name = 'peugeot 505s turbo diesel'"
            
            result = evaluate_answers(question, sample_llm_answer_dict, correct_answer, mock_connection)

            assert result == True
            assert len(output_data) == 1
            assert len(correct_output_data) == 1
            assert len(incorrect_output_data) == 0

    def test_invalid_syntax(self, mock_connection):
        with patch('sql_bot.metrics.validation.execute_query') as mock_execute_query:
            mock_execute_query.return_value = [[20000.0]]
            
            llm_answer_dict = {
                'is_valid_syntax': False,
                'model_response': 'Invalid SQL',
                'examples': 'examples ',
                'similarity_scores': [0.8, 0.9]
            }

            question = "How much is the Peugeot 505s Turbo Diesel?"
            correct_answer = "SELECT T2.price FROM data AS T1 INNER JOIN price AS T2 ON T1.ID = T2.ID WHERE T1.car_name = 'peugeot 505s turbo diesel'"

            result = evaluate_answers(question, llm_answer_dict, correct_answer, mock_connection)

            assert result == False
            assert len(output_data) == 1
            assert len(correct_output_data) == 0
            assert len(incorrect_output_data) == 1
            assert output_data[0]['llm_results'] == "Invalid Syntax"

    def test_execution_error(self, mock_connection, sample_llm_answer_dict):
        with patch('sql_bot.metrics.validation.execute_query') as mock_execute_query:
            mock_execute_query.side_effect = [Exception("SQL Error"), [[20000.0]]]
            
            question = "How much is the Peugeot 505s Turbo Diesel?"
            correct_answer = "SELECT T2.price FROM data AS T1 INNER JOIN price AS T2 ON T1.ID = T2.ID WHERE T1.car_name = 'peugeot 505s turbo diesel'"

            result = evaluate_answers(question, sample_llm_answer_dict, correct_answer, mock_connection)

            assert result == False
            assert len(output_data) == 1
            assert len(correct_output_data) == 0
            assert len(incorrect_output_data) == 1
            assert output_data[0]['llm_results'] == "Error"