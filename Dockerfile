# Use official Python image
FROM python:3.11

# Set working directory
WORKDIR /app

# Copy requirements (if available)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy rest of the application
COPY . .

# Expose Flask port (inside container)
EXPOSE 8181

# Default command to run the Flask app
CMD ["python", "main.py"]
