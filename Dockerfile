# Basic docker image for PGNumbra
# Usage:
#   docker build -t PGNumbra
#   docker run -d --name PGNumbra -P PGNumbra

FROM python:2.7-alpine

# Working directory for the application
WORKDIR /usr/src/app

# Set Entrypoint with hard-coded options
ENTRYPOINT ["python", "./shadowcheck.py"]

# Install required system packages
RUN apk add --no-cache ca-certificates
RUN apk add --no-cache bash git openssh
RUN apk add --no-cache linux-headers

COPY requirements.txt /usr/src/app/

RUN apk add --no-cache build-base \
 && pip install --no-cache-dir -r requirements.txt \
 && apk del build-base

# Copy everything to the working directory (Python files, templates, config) in one go.
COPY . /usr/src/app/