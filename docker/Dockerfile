# Docker image definition for https://github.com/bvanheu/pytoutv
FROM python:3.7-stretch
LABEL maintainers="Anthony Dahanne <anthony.dahanne@gmail.com>"
RUN pip3 install pytoutv
VOLUME /media
WORKDIR /media
ENTRYPOINT ["toutv"]
CMD [""]
