import logging
import psycopg2
import json
import azure.functions as func
import os
from email.utils import parseaddr

def main(req: func.HttpRequest, res: func.Out[func.HttpResponse]) -> None:
    logging.info('Python HTTP trigger function processed a request.')

    try:
        # Parse the JSON request body
        req_body = req.get_json()
        logging.info(f"Parsed request body: {req_body}")
    except ValueError:
        res.set(func.HttpResponse(
            "Invalid JSON input",
            status_code=400
        ))
        return

    name = req_body.get('Name')
    email = req_body.get('Email')

    # Validate presence and data type of 'Name' and 'Email'
    if not name or not isinstance(name, str) or not name.strip():
        res.set(func.HttpResponse(
            "Valid 'Name' is required",
            status_code=400
        ))
        return

    if not email or not isinstance(email, str) or not is_valid_email(email):
        res.set(func.HttpResponse(
            "Valid 'Email' is required",
            status_code=400
        ))
        return

    conn = None
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(
            dbname="postgres",
            user="postgres",
            password="vishnu@1234",
            host="bbos-database.postgres.database.azure.com",
            port="5432",
            sslmode="require"  # Ensures the connection is encrypted
        )
        cur = conn.cursor()
        # Execute SQL command
        cur.execute("INSERT INTO details (name, email) VALUES (%s, %s)", (name.strip(), email.strip()))
        conn.commit()
        cur.close()

        res.set(func.HttpResponse(
            "Record added successfully",
            status_code=200
        ))
    except psycopg2.Error as db_error:
        logging.error(f"Database error: {db_error}")
        res.set(func.HttpResponse(
            "Failed to add record to the database.",
            status_code=500
        ))
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        res.set(func.HttpResponse(
            "An unexpected error occurred.",
            status_code=500
        ))
    finally:
        if conn:
            conn.close()

def is_valid_email(email):
    """
    Validate email format using parseaddr from the email.utils module.
    """
    _, addr = parseaddr(email)
    return '@' in addr and '.' in addr
