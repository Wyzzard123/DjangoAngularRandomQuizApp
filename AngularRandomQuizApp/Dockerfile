FROM node:alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:1.19-alpine

COPY default.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist/AngularRandomQuizApp /usr/share/nginx/html
