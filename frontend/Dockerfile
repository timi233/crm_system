# Frontend: Build React app and serve with Nginx
FROM node:18 AS build
WORKDIR /app
COPY package.json package.json
RUN unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy && npm install --registry=https://registry.npmmirror.com
COPY . .
RUN unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy && npm run build

FROM nginx:alpine
RUN sed -i 's|http://dl-cdn.alpinelinux.org|http://mirrors.aliyun.com|g' /etc/apk/repositories && \
    apk add --no-cache gettext
ENV NGINX_SERVER_NAME=localhost
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/templates/default.conf.template
EXPOSE 80
CMD ["/bin/sh", "-c", "envsubst '${NGINX_SERVER_NAME}' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'"]
