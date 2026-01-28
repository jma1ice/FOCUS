# FOCUS - Minimal To-Do Site allowing for tasks, ideas, notes, and link saving

## Docker Compose

Here are the steps to get this tool running in your docker instance with Docker Compose
1. Create a folder for FOCUS and move into it
2. Save the below as `docker-compose.yml` (change the `SECRET_KEY` environment variable)
```yaml
services:
  focus:
    container_name: focus
    image: jma1ice/focus:latest
    restart: unless-stopped
    ports:
      - 3287:3287
    environment:
      - SECRET_KEY=${SECRET_KEY:-change-this-secret-key-in-production}
      - DATABASE_PATH=/app/focus.db
      - FLASK_ENV=production
    volumes:
      - focus_data:/app
    networks:
      - focus_network

volumes:
  focus_data:
    driver: local

networks:
  focus_network:
    driver: bridge

```
3. In the terminal of your choice, navigate to your FOCUS directory and run `docker compose up -d`

The dashboard will be available at `localhost:3287`
