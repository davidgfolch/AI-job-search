# base image
FROM python:3.10

# install packages
RUN apt-get update \
    && apt-get upgrade -y
RUN apt-get install -y \
    vim \
    curl \
    pandoc \
    texlive-xetex \
    texlive-fonts-recommended \
    texlive-plain-generic

# create user and home directory
RUN useradd -m -d /home/devuser -s /bin/bash devuser
USER devuser

ENV PATH=/home/devuser/.local/bin:$PATH

# upgrade pip and install python packages
RUN /usr/local/bin/python -m pip install --upgrade pip
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt