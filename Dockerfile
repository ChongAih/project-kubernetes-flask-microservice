FROM ubuntu:20.04

# Install Python pip & pipenv
RUN apt-get update && \
    apt-get install -y --no-install-recommends python3 python3-pip python3-setuptools python3-wheel && \
    pip install pipenv && \
    rm -rf /var/lib/apt/lists/*

# Define API exposed port
ARG FLASK_MICROSERVICE_PORT=5000
ARG FLASK_MICROSERVICE_ENV="prod"
EXPOSE $FLASK_MICROSERVICE_PORT
ENV FLASK_MICROSERVICE_PORT=$FLASK_MICROSERVICE_PORT
ENV FLASK_MICROSERVICE_ENV=$FLASK_MICROSERVICE_ENV

# Create and copy content to directory
WORKDIR /microservice
COPY . .

# Create volume for database
VOLUME /database

# Install all packages into the system python
RUN pipenv install --system --deploy --ignore-pipfile

ENTRYPOINT ["python3", "manage.py"]

# RUN pipenv install --system --deploy --ignore-pipfile && \
#     chmod 777 entrypoint.sh
# ENTRYPOINT ["./entrypoint.sh"]
