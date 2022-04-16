FROM node

WORKDIR /src
COPY package.json .
COPY yarn.lock .
RUN yarn install

ENV REACT_APP_ENVIRONMENT=docker
COPY . .
EXPOSE 3000
ENTRYPOINT yarn start