#!/bin/bash
# Supabase Session Pooler Connection Helper
# Works with psql directly - no Python dependencies

# Session Pooler Credentials
PGUSER="postgres.txlzlhcrfippujcmnief"
PGPASSWORD="rC@UUh9Z%*WQ"
PGHOST="aws-0-us-east-2.pooler.supabase.com"
PGPORT="5432"
PGDATABASE="postgres"

# Export for psql
export PGUSER PGPASSWORD PGHOST PGPORT PGDATABASE

CONNECTION_STRING="postgresql://${PGUSER}:${PGPASSWORD}@${PGHOST}:${PGPORT}/${PGDATABASE}"

usage() {
    echo "Usage: $0 <command> [args]"
    echo ""
    echo "Commands:"
    echo "  connection-string      - Print connection string"
    echo "  psql                   - Open interactive psql session"
    echo "  list-tables            - List all tables"
    echo "  schema <table>         - Show table schema"
    echo "  count <table>          - Count records in table"
    echo "  query '<sql>'          - Execute SELECT query"
    exit 1
}

if [ $# -lt 1 ]; then
    usage
fi

COMMAND=$1
shift

case $COMMAND in
    connection-string)
        echo "$CONNECTION_STRING"
        ;;
    psql)
        psql
        ;;
    list-tables)
        psql -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;"
        ;;
    schema)
        if [ -z "$1" ]; then
            echo "Usage: $0 schema <table_name>"
            exit 1
        fi
        psql -c "SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = '$1' ORDER BY ordinal_position;"
        ;;
    count)
        if [ -z "$1" ]; then
            echo "Usage: $0 count <table_name>"
            exit 1
        fi
        psql -c "SELECT COUNT(*) as record_count FROM $1;"
        ;;
    query)
        if [ -z "$1" ]; then
            echo "Usage: $0 query '<sql_query>'"
            exit 1
        fi
        psql -c "$1"
        ;;
    *)
        echo "Unknown command: $COMMAND"
        usage
        ;;
esac
