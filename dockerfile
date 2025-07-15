FROM python:3.10

# Set working directory
WORKDIR /app

# Copy all files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port for Railway
EXPOSE 8080

# Run gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:8080", "server:app"]
