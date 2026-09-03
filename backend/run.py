import uvicorn
import os
import sys
from app.database import engine, Base, SessionLocal
from app.generator import generate_synthetic_data
from app.agent import scan_revenue_opportunities

def main():
    print("AI Revenue Recovery Agent - Backend Initializer")
    
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        from app.models import Customer
        customer_count = db.query(Customer).count()
        if customer_count == 0:
            print("Database is empty. Seeding synthetic data...")
            generate_synthetic_data(db)
            print("Running initial agent scan to identify opportunities...")
            scan_revenue_opportunities(db)
            print("Setup complete.")
        else:
            print(f"Database is already seeded with {customer_count} customers. Skipping seeding.")
    except Exception as e:
        print(f"Error during initialization: {e}")
    finally:
        db.close()
        
    print("Starting FastAPI Uvicorn server on http://localhost:8000 ...")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()
