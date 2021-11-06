FROM ubuntu:18.04

WORKDIR /workspaces/docker_twitter
copy ./requirements.txt ./requirements.txt
RUN apt-get update
RUN apt-get install -y vim python3 python3-pip python-setuptools wget lsb-release libmysqlclient-dev
RUN pip3 install -r requirements.txt