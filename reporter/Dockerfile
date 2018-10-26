FROM node:10-alpine AS builder

COPY *.js package*.json ./
RUN npm ci && npm run build

FROM node:10-alpine

COPY --from=builder dist/coverage-reporter.js /home/node

CMD [ "node", "/home/node/coverage-reporter.js" ]
