FROM python:3.10.1-alpine

WORKDIR /app
COPY entrypoint.sh *.py /app/
COPY conf /app/conf/

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["help"]
