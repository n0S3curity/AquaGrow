# Use a slim Python image as a base for a smaller image size
FROM python:3.9

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and install Python dependencies
# Using --no-cache-dir to prevent pip from storing downloaded packages
# which keeps the image smaller.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code into the container
# This includes your main Flask app, config, logger, sensor, routes, and the static folder
COPY . .

# Expose the port that your Flask application runs on
# This should match SERVER_PORT in your config.py/main.py (default 5000)
EXPOSE 5000

# Command to run your Flask application when the container starts
# Assuming your main Flask app file is named 'main.py'
CMD ["python", "main.py"]
