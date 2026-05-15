# Frontend: Build React app and serve with Nginx
FROM node:18 AS build
WORKDIR /app
COPY package.json package.json
RUN unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy && npm install
COPY . .
RUN unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy && npm run build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
