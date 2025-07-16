# Use a minimal Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy code
COPY . /app

# Install dependencies
RUN pip install flask

# Expose Flask port
EXPOSE 5061

# Run the Flask app
CMD ["python", "app.py"]
