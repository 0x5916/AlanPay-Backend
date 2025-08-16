from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from app.utils.database import AsyncSessionDep
from app.utils.logging_config import logger


router = APIRouter(prefix="/api/admin")

@router.get("/database/{table_name}")
async def get_table_data(session: AsyncSessionDep, table_name: str):
    """
    Fetch data from a specific table in the database.
    """
    try:
        stmt = text(f"SELECT * FROM {table_name}")
        result = await session.execute(stmt)
        data = result.fetchall()
        return {"table": table_name, "data": [tuple(row) for row in data]}
    except Exception as e:
        logger.error(f"Error fetching data from {table_name}: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")