#!/bin/bash
set -e

# Run database migrations
flask db upgrade

# Start the Flask application
flask run --host=0.0.0.0
