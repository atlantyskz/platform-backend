# Stage 1: Builder
FROM python:3.10-slim AS builder

# Set working directory
WORKDIR /app

# Copy and install dependencies
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir --target=/app/dependencies -r requirements.txt

# Copy the application files
COPY . .

# Stage 2: Final image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy dependencies and application files from the builder stage
COPY --from=builder /app/dependencies /usr/local/lib/python3.10/site-packages
COPY --from=builder /app /app

# Expose the application port
EXPOSE 9000

# Define the command to run the application
CMD ["python", "main.py"]