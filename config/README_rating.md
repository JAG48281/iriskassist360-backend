# Rating Engine Configuration

This module relies on a PostgreSQL database to fetch insurance rates and add-on pricing.

## Environment Variables

The following environment variables are required for the Rating Engine to function correctly.

| Variable | Description | Required | Example |
|---|---|---|---|
| `DATABASE_URL` | Full PostgreSQL connection string | Yes | `postgresql://user:password@host:port/dbname` |
| `PGUSER` | Database username (if not in URL) | No | `postgres` |
| `PGPASSWORD` | Database password (if not in URL) | No | `secret` |

## Local Development

Ensure your `.env` file contains the `DATABASE_URL`:
```bash
DATABASE_URL=postgresql://postgres:password@localhost:5432/iriskassist360_db
```

## Railway Deployment Configuration

When deploying to Railway, you must set these variables in the **Service Settings** -> **Variables** tab.

1. **DATABASE_URL**: railway usually provides this automatically if you add a PostgreSQL plugin.
   - If not, construct it: `postgresql://${PGUSER}:${PGPASSWORD}@${PGHOST}:${PGPORT}/${PGDATABASE}`

2. **Custom Variables**:
   - Go to your Railway project.
   - Select the Backend service.
   - Click "Variables".
   - Add `ALLOW_ORIGINS` if connecting from a specific frontend domain.

_Note: The rating engine will log warnings and return default/fallback rates (0.0) if the database connection fails or tables are missing._
