FROM amazoncorretto:22-jdk
LABEL authors="charlie"

ENTRYPOINT ["top", "-b"]