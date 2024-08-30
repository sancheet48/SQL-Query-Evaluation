
import sqlglot

class SQLProcessor:
    """A class to handle SQL query processing, including validation and case-insensitive modifications."""


    def validate_sql(sql_query: str) -> bool:
        """
        Validates the SQL query using sqlglot.

        Args:
            sql_query: The SQL query to validate.

        Returns:
            True if the query is valid, False otherwise.
        """
        try:
            sqlglot.parse(sql_query)
            return True
        except sqlglot.errors.ParseError:
            return False


    def query_parser(query: str) -> str:
        """
        Parses the query to remove markdown and backticks.

        Args:
            query: The query to parse.

        Returns:
            The parsed query.
        """
        return query.replace('`sql\n', '').replace('\n`', '').replace('`', '').strip()


    def add_case_insensetiveness(query: str) -> str:
        """
        Adds case-insensitivity to the query using COLLATE NOCASE.

        Args:
            query: The query to modify.

        Returns:
            The modified query with case-insensitivity.
        """
        return query + " COLLATE NOCASE "