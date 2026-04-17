# Frontend: Build React app and serve with Nginx
FROM node:18 AS build
WORKDIR /app
COPY package.json package.json
RUN unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy && npm install
COPY . .
RUN unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy && npm run build

FROM nginx:alpine
RUN apk add --no-cache gettext
ENV NGINX_SERVER_NAME=localhost
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/templates/default.conf.template
EXPOSE 80
CMD ["/bin/sh", "-c", "envsubst '${NGINX_SERVER_NAME}' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'"]
