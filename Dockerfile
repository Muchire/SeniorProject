#Dockerfile

FROM python:3.10-slim

# set environment variables

ENV  key value PYTHONDONTWRITEBYTECODE 1
ENV key value  PYTHONUNBUFFERED 1

# set work directory

WORKDIR /app

#install dependacies

COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

#copy project files

COPY . /app/

EXPOSE 8000

# Start the server using gunicorn
CMD ["gunicorn", "PSV_Backend.PSV_Backend.wsgi:application", "--bind", "0.0.0.0:8000"]