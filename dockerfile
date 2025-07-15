# Gunakan base image Python resmi yang sudah lengkap
FROM python:3.10-slim

# Install distutils, gcc, dan pip dependencies agar numpy dan lainnya sukses
RUN apt-get update && \
    apt-get install -y python3-distutils python3-dev gcc build-essential && \
    apt-get clean

# Set working directory
WORKDIR /app

# Copy semua file ke dalam container
COPY . .

# Install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose port (Railway default = 8080)
EXPOSE 8080

# Jalankan aplikasi dengan gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "server:app"]
