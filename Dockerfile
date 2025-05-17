# Stage 1: Base image for building the app
FROM python:3.11-slim AS build

# Set working directory
WORKDIR /app

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

# Copy dependencies from build stage
COPY --from=build /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=build /app /app

# Expose port
EXPOSE 5000

ENV DB_DRIVER="ODBC Driver 17 for SQL Server" \
    DB_HOST="34.44.254.240,1433" \
    DB_NAME="JLearnDb" \
    DB_USER="sa" \
    DB_PASSWORD="Quangvinh16#" \
    DB_TRUST_SERVER_CERT="Yes"


# Run the application
CMD ["python", "app.py"]
