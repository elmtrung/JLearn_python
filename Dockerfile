# Stage 1: Base image for building the app
FROM python:3.11-slim AS build

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y \
    unixodbc \
    unixodbc-dev \
    ffmpeg \
    && ln -s /usr/lib/x86_64-linux-gnu/libodbc.so.2 /usr/lib/libodbc.so.2 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application files
COPY . .

# Stage 2: Production image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y \
    unixodbc \
    ffmpeg \
    && ln -s /usr/lib/x86_64-linux-gnu/libodbc.so.2 /usr/lib/libodbc.so.2 \
    && rm -rf /var/lib/apt/lists/*

# Copy dependencies from build stage
COPY --from=build /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=build /app /app

# Expose port
EXPOSE 5000

ENV DB_DRIVER="ODBC Driver 17 for SQL Server" \
    DB_HOST="sqlserver" \
    DB_NAME="JLearnDb" \
    DB_USER="sa" \
    DB_PASSWORD="Quangvinh16#" \
    DB_TRUST_SERVER_CERT="Yes"

# Run the application
CMD ["python", "app.py"]