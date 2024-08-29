import sqlglot

def validate_sql(sql_query):
    try:
        sqlglot.parse(sql_query)
        return True
    except sqlglot.errors.ParseError:
        return False
    

def query_parser(query: str):
    return query.replace('```sql\n', '').replace('\n```', '').replace('`', '').strip()

def add_case_insensetiveness(query:str)->str:
    return query + " COLLATE NOCASE "
