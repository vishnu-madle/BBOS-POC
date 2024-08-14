import logging
import psycopg2
import json
import azure.functions as func
import os

def main(req: func.HttpRequest, res: func.Out[func.HttpResponse]) -> None:
    logging.info('Python HTTP trigger function processed a request.')

    try:
        # Parse the JSON request body
        req_body = req.get_json()
        logging.info(f"Parsed request body: {req_body}")
    except ValueError:
        res.set(func.HttpResponse(
            "Invalid input",
            status_code=400
        ))
        return

    name = req_body.get('Name')
    email = req_body.get('Email')

    if not name or not email:
        res.set(func.HttpResponse(
            "Name and email are required",
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
            port="5432"
        )
        cur = conn.cursor()
        # Execute SQL command
        cur.execute("INSERT INTO details (name, email) VALUES (%s, %s)", (name, email))
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
