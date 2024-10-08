import logging
import psycopg2
import json
import azure.functions as func
import os
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

def main(req: func.HttpRequest, res: func.Out[func.HttpResponse]) -> None:
    logging.info('Python HTTP trigger function processed a request.')

    try:
        req_body = req.get_json()
        logging.info(f"Parsed request body: {req_body}")
    except ValueError:
        res.set(func.HttpResponse("Invalid input", status_code=400)) 
        return 

    name = req_body.get('name')
    email = req_body.get('email')
    logging.info(f"name: {name}, email: {email}")
   
    if not name or not email:
        res.set(func.HttpResponse("Name and email are required", status_code=400))
        return

    conn = None
    try:
        key_vault_url = os.environ["KEY_VAULT_URL"]
        credential = DefaultAzureCredential()
        secret_client = SecretClient(vault_url=key_vault_url, credential=credential)

        db_name = secret_client.get_secret("PostgreSQL-DBName").value
        db_user = secret_client.get_secret("PostgreSQL-User").value
        db_password = secret_client.get_secret("PostgreSQL-Password").value
        db_host = secret_client.get_secret("PostgreSQL-Host").value
        db_port = secret_client.get_secret("PostgreSQL-Port").value

        conn = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port
        )
        cur = conn.cursor()
        cur.execute("INSERT INTO details (name, email) VALUES (%s, %s)", (name, email))
        conn.commit()
        cur.close()

        res.set(func.HttpResponse("Record added successfully", status_code=200))

    except psycopg2.Error as db_error:
        logging.error(f"Database error: {db_error}")
        res.set(func.HttpResponse("Failed to add record to the database.", status_code=500))
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        res.set(func.HttpResponse("An unexpected error occurred.", status_code=500))
    finally:
        if conn:
            conn.close()
