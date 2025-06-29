from pydantic import BaseModel, Field
from typing import Optional

class ScanIn(BaseModel):
    barcode: Union[str, int] = Field(..., example="0081234567890")
    price: Optional[float] = Field(None, example=28.75)
    slot: Optional[str] = Field(None, example="A-03")   #row-rack