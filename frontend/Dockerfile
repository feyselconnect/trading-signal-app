# Frontend Dockerfile
FROM node:20-alpine as build

WORKDIR /app

COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Serve the build with a static server
FROM node:20-alpine as serve
WORKDIR /app
COPY --from=build /app/build ./build
RUN npm install -g serve
EXPOSE 3000
CMD ["serve", "-s", "build", "-l", "3000"] 