# PetroTrack Backend

## Run with Docker

Create `.env` with the required Django and Supabase values, then start the API
and PostgreSQL database:

```sh
docker compose up --build
```

The API is available at `http://localhost:8000`. Database migrations and static
file collection run automatically whenever the web container starts.

Stop the containers with `docker compose down`. To also delete the local
database volume, run `docker compose down -v`.
