"""
Vanta - FastAPI Backend
Handles wallet signatures and security for the NFT platform.
"""
from __future__ import annotations

import re
from typing import Annotated, Optional

from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel, Field

app = FastAPI(title="Vanta API", version="1.0.0")


# --- Request/Response Models ---

class SignRequest(BaseModel):
    """Request to sign a message."""
    message: str = Field(..., min_length=1, max_length=1000)
    address: str = Field(..., min_length=42, max_length=42)


class ListRequest(BaseModel):
    """Request to list NFT for sale."""
    price: float = Field(..., gt=0, le=1000)
    token_uri: str = Field(..., min_length=1, max_length=500)
    signature: str = Field(..., min_length=1)
    address: str = Field(..., min_length=42, max_length=42)


# --- Validation ---

ETH_ADDRESS_PATTERN = re.compile(r"^0x[a-fA-F0-9]{40}$")


def validate_eth_address(address: str) -> bool:
    """Validate Ethereum address format."""
    return bool(ETH_ADDRESS_PATTERN.match(address))


def validate_price(price: float) -> bool:
    """Validate price is within bounds."""
    return 0 < price <= 1000


# --- Routes ---

@app.get("/")
async def root() -> dict[str, str]:
    """Health check."""
    return {"status": "ok", "service": "Vanta API"}


@app.post("/api/sign")
async def sign_message(req: SignRequest) -> dict[str, str]:
    """
    Verify and process signing request.
    In production: verify wallet ownership via signature.
    """
    if not validate_eth_address(req.address):
        raise HTTPException(status_code=400, detail="Invalid address")
    return {"status": "accepted", "message_hash": "0x" + "00" * 32}


@app.post("/api/list")
async def list_nft(req: ListRequest) -> dict[str, str]:
    """
    Validate listing request.
    In production: verify signature, call contract.
    """
    if not validate_eth_address(req.address):
        raise HTTPException(status_code=400, detail="Invalid address")
    if not validate_price(req.price):
        raise HTTPException(status_code=400, detail="Invalid price")
    return {"status": "accepted", "listing_id": "pending"}


def run() -> None:
    """Run the API server."""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    run()