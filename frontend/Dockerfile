FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application
COPY . .

# Expose port
EXPOSE 5173

# Run development server (no build needed, supports hot reload)
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
