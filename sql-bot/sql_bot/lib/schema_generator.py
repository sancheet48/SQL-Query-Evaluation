import json
import argparse

class SchemaGenerator:
    """
    A class responsible for generating a database schema from JSON data.
    """

    def __init__(self, db_data):
        """
        Initializes the SchemaGenerator with the database data.

        Args:
            db_data (list): A list of dictionaries representing database information.
        """
        self.db_data = db_data

    def find_database(self, db_id):
        """
        Finds the database object based on the given db_id.

        Args:
            db_id (int): The ID of the database to find.

        Returns:
            dict or None: The database object if found, otherwise None.
        """
        return next((db for db in self.db_data if db["db_id"] == db_id), None)

    def generate_schema(self, db_id):
        """
        Generates a schema for the given database ID.

        Args:
            db_id (int): The ID of the database to generate the schema for.

        Returns:
            dict or None: The generated schema if successful, otherwise None.
        """
        db = self.find_database(db_id)

        if not db:
            print(f"No database found with db_id: {db_id}")
            return None

        schema = {"db_id": db_id, "tables": []}

        table_names = db["table_names_original"]
        column_names = db["column_names_original"]
        column_types = db["column_types"]
        primary_keys = self._extract_primary_keys(db)
        foreign_keys = self._extract_foreign_keys(db)

        for table_index, table_name in enumerate(table_names):
            table_schema = self._generate_table_schema(
                table_index, table_name, column_names, column_types, primary_keys, foreign_keys
            )
            schema["tables"].append(table_schema)

        return schema

    def _extract_primary_keys(self, db):
        """
        Extracts primary key indexes from the database data.

        Args:
            db (dict): The database object.

        Returns:
            set: A set of primary key indexes.
        """
        primary_keys = set()
        for pk in db["primary_keys"]:
            if isinstance(pk, list):
                primary_keys.update(pk)
            else:
                primary_keys.add(pk)
        return primary_keys

    def _extract_foreign_keys(self, db):
        """
        Extracts foreign key relationships from the database data.

        Args:
            db (dict): The database object.

        Returns:
            dict: A dictionary mapping foreign key column indexes to referenced column indexes.
        """
        return {fk[0]: fk[1] for fk in db["foreign_keys"]}

    def _generate_table_schema(self, table_index, table_name, column_names, column_types, primary_keys, foreign_keys):
        """
        Generates the schema for a single table.

        Args:
            table_index (int): The index of the table.
            table_name (str): The name of the table.
            column_names (list): A list of tuples containing column table indexes and column names.
            column_types (list): A list of column types.
            primary_keys (set): A set of primary key indexes.
            foreign_keys (dict): A dictionary mapping foreign key column indexes to referenced column indexes.

        Returns:
            dict: The generated schema for the table.
        """
        table_schema = {"table_name": table_name, "columns": []}

        for col_index, (col_table_index, col_name) in enumerate(column_names):
            if col_table_index == table_index:
                column_schema = {
                    "column_name": col_name,
                    "column_type": column_types[col_index]
                }
                if col_index in primary_keys:
                    column_schema["primary_key"] = True
                if col_index in foreign_keys:
                    column_schema["foreign_key"] = True
                table_schema["columns"].append(column_schema)

        return table_schema

def main():
    """
    The main function to handle command-line arguments and schema generation.
    """
    parser = argparse.ArgumentParser(description="Generate schema from JSON file.")
    parser.add_argument("json_file", help="Path to the JSON file containing database schema.")
    parser.add_argument("db_id", help="Database ID to generate schema for.")
    args = parser.parse_args()

    with open(args.json_file, "r") as f:
        db_data = json.load(f)

    generator = SchemaGenerator(db_data)
    schema = generator.generate_schema(args.db_id)

    if schema:
        with open("sql_bot/lib/llm_schema.txt", "w") as file:
            json.dump(schema, file, indent=2)

if __name__ == "__main__":
    main()