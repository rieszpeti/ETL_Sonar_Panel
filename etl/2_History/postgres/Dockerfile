FROM postgres:latest
ADD ./sql/init.sql /docker-entrypoint-initdb.d/
ENTRYPOINT ["docker-entrypoint.sh"]
EXPOSE 5434
CMD ["postgres"]