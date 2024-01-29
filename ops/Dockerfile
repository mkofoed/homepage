# Use an official Python runtime as a parent image
FROM python:3.12-alpine as builder

# Set the working directory in the container to /homepage
WORKDIR /homepage

# Copy the current directory contents into the container at /homepage
COPY . /homepage/

# Install any needed packages specified in requirements.txt
RUN pip install --upgrade pip \
    && pip install "poetry==1.7.1" \
    && poetry config virtualenvs.create false \
    && cd ./ops \
    && poetry install $(test "$YOUR_ENV" == production && echo "--no-dev") --no-interaction --no-ansi

# Start a new stage and copy over the artifacts we need from the previous stage
FROM python:3.12-alpine

WORKDIR /homepage
COPY --from=builder /homepage /homepage
