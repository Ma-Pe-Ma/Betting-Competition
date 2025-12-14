ARG NODE_VERSION=latest
ARG NGINX_VERSION=latest

FROM node:${NODE_VERSION} AS builder

WORKDIR /app
COPY package.json package-lock.json ./

RUN --mount=type=cache,target=/root/.npm npm ci

COPY . .

RUN npm run build 

FROM nginx:${NGINX_VERSION} AS runner

EXPOSE 80
EXPOSE 443

COPY --chown=nginx:nginx --from=builder /app/dist/*/browser /usr/share/nginx/html

ENTRYPOINT ["nginx", "-c", "/etc/nginx/nginx.conf", "-g", "daemon off;"]
