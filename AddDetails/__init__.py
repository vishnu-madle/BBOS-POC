import logging
import psycopg2
import json
import azure.functions as func
import os
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    try:
        # Parse the JSON request body
        req_body = req.get_json()
        logging.info(f"Parsed request body: {req_body}")
    except ValueError:
        return func.HttpResponse(
            "Invalid input",
            status_code=400
        )

    name = req_body.get('name')
    email = req_body.get('email')

    if not name or not email:
        return func.HttpResponse(
            "Name and email are required",
            status_code=400
        )

    conn = None
    try:
        # Retrieve Key Vault URL from environment variables
        key_vault_url = os.environ.get("KEY_VAULT_URL")
        if not key_vault_url:
            raise EnvironmentError("KEY_VAULT_URL environment variable not found")

        # Authenticate using the managed identity
        credential = DefaultAzureCredential()

        # Create a client to access secrets in Key Vault
        secret_client = SecretClient(vault_url=key_vault_url, credential=credential)

        # Retrieve PostgreSQL credentials from Key Vault
        db_name = secret_client.get_secret("PostgreSQL-DBName").value
        db_user = secret_client.get_secret("PostgreSQL-User").value
        db_password = secret_client.get_secret("PostgreSQL-Password").value
        db_host = secret_client.get_secret("PostgreSQL-Host").value
        db_port = secret_client.get_secret("PostgreSQL-Port").value

        # Connect to PostgreSQL
        conn = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port
        )

        with conn.cursor() as cur:
            # Execute SQL command
            cur.execute("INSERT INTO details (name, email) VALUES (%s, %s)", (name, email))
            conn.commit()

        return func.HttpResponse(
            "Record added successfully",
            status_code=200
        )

    except psycopg2.Error as db_error:
        logging.error(f"Database error: {db_error}")
        return func.HttpResponse(
            "Failed to add record to the database.",
            status_code=500
        )
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return func.HttpResponse(
            "An unexpected error occurred.",
            status_code=500
        )
    finally:
        if conn:
            try:
                conn.close()
            except psycopg2.Error as close_error:
                logging.error(f"Error closing connection: {close_error}")
