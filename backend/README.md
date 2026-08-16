# FAST API Backend

uv run fastapi dev src/homestock_backend/main.py

# Local DB

1. Please download docker for local db.
2. Run to create a container name "homestock-db". Set the postgres superuser password to <insert password>, first db name to be 'home_inventory'. Publishes the port 5432(mac) to 5432(container). Mount a named volume 'homestock-pgdata' to '/var/lib/postgresql/data' in the container. '-d' to run this in the background and use the image postgres version 16

```
docker run --name homestock-db \
  -e POSTGRES_PASSWORD=<insert password> \
  -e POSTGRES_DB=home_inventory \
  -p 5432:5432 \
  -v homestock-pgdata:/var/lib/postgresql/data \
  -d postgres:16
```

3. Create the application role
   Open an interactive psql session as the super user

- docker exec -it homestock-db psql -U postgres -d home_inventory

Create a new role that focus only on connecting to home_inventory db. Role name is called 'homestock_app'.

- CREATE ROLE homestock_app WITH LOGIN PASSWORD '<insert password>';

Grant connection between the db and role

- GRANT CONNECT ON DATABASE home_inventory TO homestock_app;

Grant permission for the role homestock_app to see objects in the schema

- GRANT USAGE, CREATE ON SCHEMA public TO homestock_app;

4. Create config files (.env)

- Refer to .env.example
