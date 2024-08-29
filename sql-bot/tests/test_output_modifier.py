import pytest
import sys
import os
# Add the root directory to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from sql_bot.lib.output_modifier import SQLProcessor 



@pytest.mark.parametrize(
    "sql_query, expected_result",
    [
        ("SELECT * FROM users;", True),
        ("SELECT name FROM users WHERE age > 25 ORDER BY name;", True),
        ("INSERT INTO users (name, age) VALUES ('John Doe', 30);", True),
        ("INVALID SQL QUERY", False),
        ("SELECT * FROM users WHERE name LIKE '%John%'", True),
        ("UPDATE users SET age = 35 WHERE name = 'Jane Doe';", True),
        ("DELETE FROM users WHERE age < 18;", True),
    ],
)
def test_validate_sql(sql_query, expected_result):
    assert SQLProcessor.validate_sql(sql_query) == expected_result

@pytest.mark.parametrize(
    "query, expected_query",
    [
        ("```sql\nSELECT * FROM users;\n```", "SELECT * FROM users;"),
        ("```sql\nSELECT * FROM users;\n``` ", "SELECT * FROM users;"),
        ("`SELECT * FROM users;`", "SELECT * FROM users;"),
        ("SELECT * FROM users;", "SELECT * FROM users;"),
    ],
)
def test_query_parser(query, expected_query):
    assert SQLProcessor.query_parser(query) == expected_query

@pytest.mark.parametrize(
    "query, expected_query",
    [
        ("SELECT * FROM users", "SELECT * FROM users COLLATE NOCASE "),
        
    ],
)
def test_add_case_insensetiveness(query, expected_query):
    assert SQLProcessor.add_case_insensetiveness(query) == expected_query
