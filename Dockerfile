# Use lightweight Python base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy project files into container
COPY . /app

# Install dependencies
# (If requirements.txt is in demoApp/, adjust the path accordingly)
RUN pip install --no-cache-dir -r demoApp/requirements.txt

# Expose Django's default port
EXPOSE 8000

# Run Django bound to all interfaces
CMD ["python3", "demoApp/manage.py", "runserver", "0.0.0.0:8000"]
