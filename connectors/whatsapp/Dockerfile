# UniFlow WhatsApp connector image. Built by deploy/docker-compose.yml.
# Settings come from the environment (deploy/uniflow.env), not a .env file; the login
# session lives in the /app/auth volume, so a restart doesn't need a new pairing code.
FROM node:24-slim
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --omit=dev
COPY src ./src
RUN mkdir -p /app/auth && chown -R node /app/auth
USER node
CMD ["node", "src/index.js"]
