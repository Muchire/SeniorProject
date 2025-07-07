# Use official Python image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory inside the container
WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the full project
COPY . /app/

# Set PYTHONPATH to find your Django project
ENV PYTHONPATH="/app/PSV_Backend"

# Collect static files (optional, uncomment if needed)
# RUN python manage.py collectstatic --noinput

# Expose port 8000 (Gunicorn will listen here)
EXPOSE 8000

# Run Gunicorn server using your Django project's WSGI module
CMD ["gunicorn", "PSV_Backend.wsgi:application", "--bind", "0.0.0.0:8000"]
