# Stage 1: Base image for building the app
FROM python:3.11-slim AS build

WORKDIR /app

# Install system dependencies for building (if pyodbc compiles from source)
# and MS ODBC Driver prerequisites
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    unixodbc-dev \
    # ffmpeg if needed during build, otherwise move to final stage
    # ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Add Microsoft's official repository for ODBC driver
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/$(lsb_release -rs)/prod.list > /etc/apt/sources.list.d/mssql-release.list

# Install MS ODBC Driver (and tools if needed for debugging, e.g., sqlcmd)
# ACCEPT_EULA=Y is important
RUN apt-get update && \
    ACCEPT_EULA=Y apt-get install -y --no-install-recommends \
    msodbcsql17 \
    # mssql-tools \ # Uncomment if you need sqlcmd for testing
    && rm -rf /var/lib/apt/lists/*
# RUN echo 'export PATH="$PATH:/opt/mssql-tools/bin"' >> ~/.bashrc # if mssql-tools installed

# Symlink for libodbc.so.2 (may or may not be strictly necessary after installing unixodbc AND msodbcsql)
# but good to have if pyodbc specifically looks for it in /usr/lib
# The actual path might vary slightly based on the base image and installed packages.
# Verify this path inside the container if issues persist.
# RUN ln -s /usr/lib/x86_64-linux-gnu/libodbc.so.2 /usr/lib/libodbc.so.2

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Stage 2: Production image
FROM python:3.11-slim

WORKDIR /app

# Install runtime system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    unixodbc \
    ffmpeg \
    curl gnupg \ 
    && rm -rf /var/lib/apt/lists/*

# Add Microsoft's official repository for ODBC driver
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/$(lsb_release -rs)/prod.list > /etc/apt/sources.list.d/mssql-release.list

# Install MS ODBC Driver
RUN apt-get update && \
    ACCEPT_EULA=Y apt-get install -y --no-install-recommends \
    msodbcsql17 \
    && rm -rf /var/lib/apt/lists/*

# Symlink for libodbc.so.2 - ensure the source path is correct for your slim image
# Often unixodbc package creates /usr/lib/x86_64-linux-gnu/libodbc.so.2
# And some applications or pyodbc might look for it in /usr/lib/libodbc.so.2
# This might not be needed if the driver and pyodbc find it correctly.
# Check if /usr/lib/x86_64-linux-gnu/libodbc.so.2 exists first.
# If it does, you can create the symlink.
# RUN if [ -f /usr/lib/x86_64-linux-gnu/libodbc.so.2 ]; then \
#       ln -s /usr/lib/x86_64-linux-gnu/libodbc.so.2 /usr/lib/libodbc.so.2; \
#     fi
# A more robust way for the symlink if paths differ:
# RUN apt-get update && apt-get install -y odbcinst && \
#     ln -s $(odbcinst -j | grep 'DRIVERS' | cut -d: -f2 | xargs -I{} find {} -name libodbc.so.2) /usr/lib/libodbc.so.2 \
#     && rm -rf /var/lib/apt/lists/* && apt-get purge -y --auto-remove odbcinst

COPY --from=build /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=build /app /app

# Ensure pyodbc is installed (should come from requirements.txt copied from build)
# RUN pip install pyodbc # This should not be needed if requirements.txt is correct and handled in build

EXPOSE 5000

ENV DB_DRIVER="ODBC Driver 17 for SQL Server" \
    DB_HOST="sqlserver" \
    DB_NAME="JLearnDb" \
    DB_USER="sa" \
    DB_PASSWORD="Quangvinh16#" \
    DB_TRUST_SERVER_CERT="Yes"

CMD ["python", "app.py"]