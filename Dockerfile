# Use a slim Python base image
FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install any system dependencies you might need
RUN apt-get update && apt-get install -y --no-install-recommends \
    tzdata \
 && rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container
WORKDIR /app

# Copy requirements.txt first (better for caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project files
COPY . .

# Expose the port Streamlit will run on
EXPOSE 8501

# Run the Streamlit app, binding to 0.0.0.0 so it's accessible outside the container
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=${PORT:-8501}"]
