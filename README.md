# Invoice Extractor - AI-Powered Document Processing System

A full-stack application for extracting structured data from invoices using AI/LLM technology. Built with Next.js frontend, Flask backend, Celery workers, and PostgreSQL database, all orchestrated with Docker Compose.

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- OpenAI API key ([Get one here](https://platform.openai.com/))

### Setup

1. **Create environment file**:

   ```bash
   echo "OPENAI_API_KEY=your_openai_api_key_here" > backend/.env
   echo "DATABASE_URL=postgresql://invoice_user:invoice_pass@db:5432/invoice_db" >> backend/.env
   ```

2. **Start services**:

   ```bash
   docker-compose up --build
   ```

3. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:5000

## 📋 Features

- **Document Upload**: Drag-and-drop interface for PDF and image invoices
- **AI-Powered Extraction**: Uses OpenAI GPT-4o-mini to extract structured data
- **Real-time Processing**: Asynchronous processing with Celery workers
- **Data Management**: View, edit, and save extracted invoice data
- **Statistics Dashboard**: View total orders, value, and averages
- **Responsive UI**: Modern interface with real-time updates

## 🏗️ Architecture

```
Frontend (Next.js) → API (Flask) → Worker (Celery) → OpenAI API
                              ↓
                         PostgreSQL
                              ↓
                         Redis (Queue)
```

### Technology Stack

**Frontend**

- Next.js 13+ with TypeScript
- React with TailwindCSS
- SWR for data fetching
- Formik for form management
- React Dropzone for file uploads

**Backend**

- Flask with Pydantic validation
- Gunicorn for production
- Celery workers for async processing
- PostgreSQL database
- Redis for task queue

**Infrastructure**

- Docker Compose orchestration
- Local file storage (can switch to S3)

## 📁 Project Structure

```
invoice-extractor/
├── backend/
│   ├── app.py              # Flask API routes
│   ├── models.py           # Database models
│   ├── schemas.py          # Pydantic validation
│   ├── tasks.py            # Celery tasks
│   ├── tests/              # Backend tests
│   └── requirements.txt
├── frontend/
│   ├── app/                # Next.js app directory
│   ├── __tests__/          # Frontend tests
│   └── package.json
├── sample-invoices/        # Sample invoice PDFs
└── docker-compose.yml
```

## 🗄️ Database Schema

**SalesOrderHeader**

- Order/invoice numbers, dates
- Customer information
- Financial totals (subtotal, tax, total)
- Processing status

**SalesOrderDetail**

- Product information
- Quantities, prices, discounts
- Line totals

## 🔌 API Endpoints

- `GET /api/health` - Health check
- `POST /api/upload` - Upload invoice (queues Celery task)
- `GET /api/orders` - List all orders
- `GET /api/orders/<id>` - Get specific order
- `PUT /api/orders/<id>` - Update order
- `DELETE /api/orders/<id>` - Delete order
- `GET /api/stats` - Get statistics
- `GET /api/tasks/<task_id>` - Get task status

## 🧪 Testing

### Backend Tests

```bash
cd backend
pytest
```

### Frontend Tests

```bash
cd frontend
npm test
npm run test
```

## 📄 Sample Invoices

Sample invoice PDFs are available in the `sample-invoices/` directory:

- `invoice_standard.pdf` - Standard invoice format with 2 line items
- `invoice_services.pdf` - Service-based invoice (Acme Corporation)
- `invoice_multiple_items.pdf` - Invoice with 3 line items (Tech Solutions Inc.)
- `invoice_trading.pdf` - Trading company invoice with widget packages
- `invoice_simple.pdf` - Simple single-item invoice (Small Business LLC)

Upload these through the web interface to test the extraction system. To generate more samples:

```bash
cd backend && python generate_sample_invoices.py
```

## 🔄 Data Flow

1. **Upload**: User uploads PDF/image → Saved to disk
2. **Queue**: API creates order record → Queues Celery task
3. **Process**: Worker extracts text → Calls OpenAI API → Parses JSON
4. **Store**: Updates order with extracted data → Saves line items
5. **Update**: Frontend polls for updates → Displays results

## 🚀 Scaling Strategies

**Current**: Monolithic Flask, single PostgreSQL, direct OpenAI calls

**Production Recommendations**:

- **Backend**: Multiple Flask instances behind load balancer, Celery workers
- **Database**: Read replicas, connection pooling, indexing
- **Storage**: Cloud storage (S3/Azure/GCS) instead of local files
- **Queue**: Redis for task queue and caching
- **Monitoring**: Logging, APM, error tracking (Sentry)
- **Security**: Authentication, rate limiting, encryption

## 🛠️ Development

### Running Locally

```bash
# Backend
cd backend
pip install -r requirements.txt
python app.py

# Frontend
cd frontend
npm install
npm run dev
```

### Using Docker

```bash
docker-compose up --build
```

### Common Commands

```bash
make up          # Start services
make down        # Stop services
make logs        # View logs
make test        # Run tests
make db-shell    # Access database
```

## 🐛 Troubleshooting

### Database Connection Error: "database 'invoice_user' does not exist"

This error occurs when PostgreSQL tries to connect before the database is fully initialized.

**Solution:**

```bash
# Reset and restart services
docker-compose down -v
docker-compose up --build

# Or wait for database to be ready
docker-compose up -d db
docker-compose logs -f db  # Wait for "database system is ready"
docker-compose up backend worker frontend
```

### Other Common Issues

- **OpenAI API Errors**: Verify API key in `backend/.env`
- **Database Connection**: Wait for DB to be healthy (check `docker-compose logs db`)
- **File Upload**: Check file size limits (16MB max)
- **Python 3.13 Issues**: See `backend/PYTHON_VERSION.md` for compatibility notes
- **Celery Worker**: Check Redis is running and worker logs

## 📝 License

This project is provided as-is for demonstration purposes.
