# Use an official Python runtime as a parent image
FROM python:3.9-slim-buster

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# Using --no-cache-dir to reduce image size
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container at /app
COPY . .

# Make port 5000 available to the world outside this container
# (This is the port Flask typically runs on. If your app runs on a different port, change this.)
EXPOSE 5000

# Define environment variables (can be overridden by docker-compose or run command)
# FLASK_APP is already set in .env, which docker-compose passes.
# FLASK_ENV is also passed by docker-compose.

# Command to run the application using Flask's built-in server.
# For production, you would typically use a WSGI server like Gunicorn.
# Example with Gunicorn: CMD ["gunicorn", "--bind", "0.0.0.0:5000", "run:app"]
# For development with live reload, this is fine when used with volume mounts.
CMD ["flask", "run", "--host=0.0.0.0"]
