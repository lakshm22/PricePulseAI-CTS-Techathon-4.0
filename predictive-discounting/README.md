# PricePulse

AI-assisted predictive discounting for supermarket inventory.

## Workflow

Sales + inventory + expiry → demand prediction → unsold-risk score → 10–20% discount recommendation → manager approval → PostgreSQL price update → Excel synchronization → barcode billing.

## Stack

- Frontend: React + Vite
- Backend: Python + FastAPI
- Database: PostgreSQL
- ML/data: Python, NumPy, pandas, scikit-learn
- Excel synchronization: openpyxl
- Deployment: Render native Python service

No Docker is required.

## Run locally

### PostgreSQL
Create a database named `predictive_discounting`, then set `backend/.env`:

```env
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/DB_name
FRONTEND_URL=http://localhost:5173
EXCEL_FILE_PATH=excel/store_inventory.xlsx
```

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

In another terminal:

```bash
cd backend
python -m app.seed
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open the Vite URL shown in the terminal.

## Manager approval

`POST /api/apply-discount`

The manager chooses 10%, 15%, or 20% when that value is inside the AI-recommended range. The backend:

1. Validates the selected discount.
2. Calculates the new price from MRP.
3. Updates `products.current_price` in PostgreSQL.
4. Records an approval event.
5. Updates `excel/store_inventory.xlsx` automatically.
6. Records the Excel synchronization.

PostgreSQL is the source of truth; Excel is the operational spreadsheet synchronized from it.

## Billing

`POST /api/billing/scan`

Send a barcode and quantity. Billing receives the current approved price automatically. No manual discount calculation is required.

## Important deployment note

Render's default filesystem is ephemeral. For a real store-maintained cloud workbook, replace the local `openpyxl` adapter in `excel_service.py` with a cloud Excel/OneDrive/SharePoint connector, while keeping PostgreSQL as the source of truth. The local adapter is suitable for the hackathon/demo workbook.
