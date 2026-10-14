# Widget Dockerfile
FROM node:20-alpine AS build

WORKDIR /app

ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build:demo

# Serve with lightweight static server
FROM node:20-alpine
RUN npm install -g serve
COPY --from=build /app/dist /app/dist

EXPOSE 3000
CMD ["serve", "-s", "/app/dist", "-l", "3000"]
