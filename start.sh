#!/bin/bash

# Ensure we are in the project root
cd "$(dirname "$0")"

# Check if .env exists, if not create from example
if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
fi

# Install dependencies
echo "Installing dependencies..."
python3 -m pip install -r requirements.txt

# Check DB
echo "Checking database connection..."
python3 -c "
import os
from dotenv import load_dotenv
import pymysql

load_dotenv()

host = os.getenv('MYSQL_HOST', 'localhost')
port = int(os.getenv('MYSQL_PORT', 3306))
user = os.getenv('MYSQL_USER', 'root')
password = os.getenv('MYSQL_PASSWORD', '')
dbname = os.getenv('MYSQL_DB', 'personal_vault')
socket = os.getenv('MYSQL_SOCKET')

print(f'Connecting to MySQL as {user}...')
try:
    conn = None
    if socket and os.path.exists(socket):
        print(f'Using Unix Socket: {socket}')
        try:
            conn = pymysql.connect(unix_socket=socket, user=user, password=password, connect_timeout=5)
        except pymysql.err.OperationalError:
            print('Socket connection with password failed, trying without password...')
            conn = pymysql.connect(unix_socket=socket, user=user, password='', connect_timeout=5)
    
    if not conn:
        print(f'Using TCP/IP: {host}:{port}')
        try:
            conn = pymysql.connect(host=host, port=port, user=user, password=password, connect_timeout=5)
        except pymysql.err.OperationalError:
            print('TCP connection with password failed, trying without password...')
            try:
                conn = pymysql.connect(host=host, port=port, user=user, password='', connect_timeout=5)
            except pymysql.err.OperationalError:
                 print('TCP connection failed, trying default unix socket /tmp/mysql.sock...')
                 conn = pymysql.connect(unix_socket='/tmp/mysql.sock', user=user, password=password, connect_timeout=5)
        
    print('Connected to MySQL server.')
    cursor = conn.cursor()
    cursor.execute(f'CREATE DATABASE IF NOT EXISTS {dbname} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci')
    print(f'Database {dbname} ensured.')
    conn.close()
except pymysql.err.OperationalError as e:
    print(f'Operational Error: {e}')
    print(f'Please check if MySQL is running on {host}:{port} and the password for user {user} is correct.')
    exit(1)
except Exception as e:
    print(f'Error creating database: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo "Failed to initialize database. Please check your .env configuration and ensure MySQL is running."
    exit 1
fi

# Start Backend (Uvicorn)
echo "Starting PIKA on http://localhost:8877 ..."

# Check if port 8877 is already in use
if lsof -i :8877 -sTCP:LISTEN -t >/dev/null; then
    echo "Port 8877 is already in use. Assuming PIKA is running."
else
    # Start in background
    nohup python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8877 > backend.log 2>&1 &
    echo "PIKA started in background. Logs: backend.log"
    # Wait for server to start
    sleep 2
fi
