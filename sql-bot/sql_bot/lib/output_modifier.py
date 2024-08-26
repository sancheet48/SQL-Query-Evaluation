import sqlglot

def validate_sql(sql_query):
    try:
        sqlglot.parse(sql_query)
        return True
    except sqlglot.errors.ParseError:
        return False