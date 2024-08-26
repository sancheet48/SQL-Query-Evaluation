import json
import sys

def load_json_file(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def find_db_schema(data, target_db_id):
    return next((item for item in data if item['db_id'] == target_db_id), None)

def create_schema(db_schema):
    if not db_schema:
        return None

    schema = {
        "db_id": db_schema['db_id'],
        "tables": []
    }

    for i, table_name in enumerate(db_schema['table_names_original']):
        table = {
            "table_name": table_name,
            "columns": []
        }

        # Add columns
        for j, (table_id, column_name) in enumerate(db_schema['column_names_original']):
            if table_id == i:
                column = {
                    "column_name": column_name,
                    "column_type": db_schema['column_types'][j]
                }
                if j in db_schema['primary_keys']:
                    column["primary_key"] = True
                table["columns"].append(column)

        # Add primary keys for composite keys
        if isinstance(db_schema['primary_keys'][-1], list) and db_schema['primary_keys'][-1][0] in [col['column_name'] for col in table['columns']]:
            table["primary_keys"] = [{"column_name": db_schema['column_names_original'][pk][1]} for pk in db_schema['primary_keys'][-1]]

        # Add foreign keys
        foreign_keys = []
        for fk in db_schema['foreign_keys']:
            if db_schema['column_names_original'][fk[0]][0] == i:
                foreign_key = {
                    "column_name": db_schema['column_names_original'][fk[0]][1],
                    "referenced_table": db_schema['table_names_original'][db_schema['column_names_original'][fk[1]][0]],
                    "referenced_column": db_schema['column_names_original'][fk[1]][1]
                }
                foreign_keys.append(foreign_key)
        
        if foreign_keys:
            table["foreign_keys"] = foreign_keys

        schema["tables"].append(table)

    return schema

def main():
    if len(sys.argv) != 3:
        print("Usage: python script.py <json_file_path> <db_id>")
        sys.exit(1)

    json_file_path = sys.argv[1]
    target_db_id = sys.argv[2]

    data = load_json_file(json_file_path)
    db_schema = find_db_schema(data, target_db_id)

    if not db_schema:
        print(f"No schema found for db_id: {target_db_id}")
        sys.exit(1)

    schema = create_schema(db_schema)
    with open("sql_bot/lib/llm_schema.txt", "w") as file:
        json.dump(schema, file, indent=2)

    print("Schema created successfully!")


if __name__ == "__main__":
    main()