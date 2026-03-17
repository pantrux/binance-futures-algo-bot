FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
COPY apps/web/package.json apps/web/package.json
RUN npm install

FROM node:22-alpine AS builder
WORKDIR /app
ARG NEXT_PUBLIC_API_URL
ARG SYNOLOGY_API_BASE_URL
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
ENV SYNOLOGY_API_BASE_URL=${SYNOLOGY_API_BASE_URL}
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build:web

FROM node:22-alpine AS runner
WORKDIR /app
ARG NEXT_PUBLIC_API_URL
ARG SYNOLOGY_API_BASE_URL
ENV NODE_ENV=production
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
ENV SYNOLOGY_API_BASE_URL=${SYNOLOGY_API_BASE_URL}
COPY --from=builder /app .
EXPOSE 3000
CMD ["npm", "--workspace", "apps/web", "run", "start"]
