from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg2
import json
import os
from typing import Dict, Any, List
from datetime import datetime
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Viz PoC API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection with better error handling
def get_db_connection():
    try:
        connection_params = {
            "host": os.getenv("DB_HOST"),
            "database": os.getenv("DB_NAME"),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
            "port": os.getenv("DB_PORT")
        }

        
        logger.info(f"Attempting to connect to database at {connection_params['host']}:{connection_params['port']}")
        
        conn = psycopg2.connect(**connection_params)
        return conn
    except psycopg2.Error as e:
        logger.error(f"Database connection failed: {e}")
        raise e

# Pydantic models
class QueryRequest(BaseModel):
    query: str

class ChartConfig(BaseModel):
    chart_type: str
    data: List[Dict[str, Any]]
    config: Dict[str, Any]

@app.get("/")
async def root():
    return {"message": "AI Viz PoC API is running"}

@app.get("/health")
async def health_check():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        return {
            "status": "healthy", 
            "database": "connected",
            "db_host": os.getenv("DB_HOST", "localhost"),
            "db_name": os.getenv("DB_NAME", "vizpoc")
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

@app.get("/debug/db-config")
async def debug_db_config():
    """Debug endpoint to check database configuration"""
    return {
        "DB_HOST": os.getenv("DB_HOST", "localhost"),
        "DB_NAME": os.getenv("DB_NAME", "vizpoc"),
        "DB_USER": os.getenv("DB_USER", "admin"),
        "DB_PORT": os.getenv("DB_PORT", "5432"),
        "DB_PASSWORD": os.getenv("DB_PASSWORD")
    }

@app.get("/data/sales")
async def get_sales_data():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # First check if table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'sales_data'
            );
        """)
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="sales_data table not found. Please run database initialization scripts.")
        
        cursor.execute("SELECT * FROM sales_data ORDER BY date DESC LIMIT 100")
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        
        data = []
        for row in rows:
            # Convert date objects to strings for JSON serialization
            row_dict = {}
            for i, value in enumerate(row):
                if isinstance(value, datetime):
                    row_dict[columns[i]] = value.isoformat()
                else:
                    row_dict[columns[i]] = value
            data.append(row_dict)
        
        cursor.close()
        conn.close()
        return {"data": data, "count": len(data)}
    except psycopg2.Error as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query/text-to-viz")
async def text_to_visualization(request: QueryRequest):
    """Convert natural language query to visualization config"""
    try:
        # Simple rule-based approach for PoC
        query_lower = request.query.lower()
        
        # Get data from database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if "sales by region" in query_lower:
            cursor.execute("""
                SELECT region, SUM(sales_amount) as total_sales 
                FROM sales_data 
                GROUP BY region
                ORDER BY total_sales DESC
            """)
            data = [{"region": row[0], "total_sales": float(row[1])} for row in cursor.fetchall()]
            chart_config = {
                "chart_type": "bar",
                "data": data,
                "config": {
                    "x": "region",
                    "y": "total_sales",
                    "title": "Sales by Region"
                }
            }
        elif "sales over time" in query_lower:
            cursor.execute("""
                SELECT date, SUM(sales_amount) as total_sales 
                FROM sales_data 
                GROUP BY date 
                ORDER BY date
            """)
            data = [{"date": row[0].isoformat(), "total_sales": float(row[1])} for row in cursor.fetchall()]
            chart_config = {
                "chart_type": "line",
                "data": data,
                "config": {
                    "x": "date",
                    "y": "total_sales",
                    "title": "Sales Over Time"
                }
            }
        else:
            # Default: all sales data
            cursor.execute("SELECT region, product, sales_amount FROM sales_data LIMIT 20")
            data = [{"region": row[0], "product": row[1], "sales_amount": float(row[2])} for row in cursor.fetchall()]
            chart_config = {
                "chart_type": "table",
                "data": data,
                "config": {
                    "title": "Sales Data"
                }
            }
        
        cursor.close()
        conn.close()
        
        # Store query in database
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO user_queries (query_text, chart_config) VALUES (%s, %s)",
                (request.query, json.dumps(chart_config))
            )
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            logger.warning(f"Failed to store query: {e}")
        
        return chart_config
        
    except psycopg2.Error as e:
        logger.error(f"Database error in text_to_viz: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in text_to_viz: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)