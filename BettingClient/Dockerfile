ARG NODE_VERSION=latest
ARG NGINX_VERSION=latest

FROM node:${NODE_VERSION} AS builder

WORKDIR /app
COPY package.json package-lock.json ./

RUN --mount=type=cache,target=/root/.npm npm ci

COPY . .

RUN npx ng build --configuration=production --output-path=dist/en --base-href="/"
RUN npx ng build --configuration=hu-build --output-path=dist/hu --base-href="/hu/"

FROM nginx:${NGINX_VERSION} AS runner

EXPOSE 80
EXPOSE 443

COPY --chown=nginx:nginx --from=builder /app/dist/en/browser/. /usr/share/nginx/html
COPY --chown=nginx:nginx --from=builder /app/dist/hu/browser/hu/. /usr/share/nginx/html/hu

ENTRYPOINT ["nginx", "-c", "/etc/nginx/nginx.conf", "-g", "daemon off;"]
