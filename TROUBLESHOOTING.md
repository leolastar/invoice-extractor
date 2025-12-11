# Troubleshooting Guide

## Database Connection Issues

### Error: "database 'invoice_user' does not exist"

This error occurs when PostgreSQL tries to connect to a database named after the username instead of the actual database name.

**Solution:**
1. Ensure the database is fully initialized:
   ```bash
   docker-compose down -v
   docker-compose up -d db
   # Wait for database to be ready
   docker-compose logs db | grep "database system is ready"
   ```

2. Verify the connection string format:
   ```
   postgresql://username:password@host:port/database_name
   ```
   Should be: `postgresql://invoice_user:invoice_pass@db:5432/invoice_db`

3. Check environment variables:
   ```bash
   docker-compose exec backend env | grep DATABASE_URL
   ```

4. Reset database volumes if needed:
   ```bash
   docker-compose down -v
   docker-compose up --build
   ```

## Common Issues

### OpenAI API Errors
- Verify API key in `backend/.env`
- Check API key has sufficient credits
- Verify network connectivity to OpenAI

### Celery Worker Not Processing
- Check Redis is running: `docker-compose ps redis`
- Check worker logs: `docker-compose logs worker`
- Verify Celery broker URL is correct

### Frontend Not Connecting to Backend
- Verify `NEXT_PUBLIC_API_URL` is set correctly
- Check backend is running: `docker-compose ps backend`
- Check CORS configuration in backend

### Database Migration Issues
- Database tables are auto-created on startup
- If tables don't exist, check backend logs for errors
- Manually create if needed: `docker-compose exec backend python -c "from app import app, db; app.app_context().push(); db.create_all()"`

