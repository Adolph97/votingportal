from fastapi import FastAPI, Request, Depends, Form, HTTPException, Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from pathlib import Path
import os
from fastapi.middleware.cors import CORSMiddleware
from . import models, database
from .config import settings
from fastapi.security import HTTPBasic
import secrets
import json
import requests
from typing import Optional
from urllib.parse import urlencode

app = FastAPI()

# Mount static files - update the directory path
app.mount("/static", StaticFiles(directory="static"), name="static")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# For Vercel, we need to handle static files differently
if not os.environ.get("VERCEL"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates - make sure this points to your templates directory
templates = Jinja2Templates(directory="templates")

# Create database tables
models.Base.metadata.create_all(bind=database.engine)

# Initialize security
security = HTTPBasic()

# Session storage (in production, use Redis or a database)
sessions = {}

VOTE_COST = 50  # Cost per vote in Naira

def set_admin_cookie(response: Response, value: str):
    response.set_cookie(
        key="admin_access",
        value=value,
        httponly=True,
        max_age=3600,  # 1 hour
        secure=False,  # Set to True in production with HTTPS
    )

def verify_admin_cookie(request: Request) -> bool:
    cookie = request.cookies.get("admin_access")
    if not cookie:
        return False
    # Verify the cookie value (you might want to make this more secure)
    return cookie == f"admin_{settings.ADMIN_PASSWORD}"

@app.get("/")
async def index(request: Request, db: Session = Depends(database.get_db)):
    candidates_folder = Path("static/assets/candidates")
    candidates = []
    
    if not candidates_folder.exists():
        os.makedirs(candidates_folder)
    
    for filename in os.listdir(candidates_folder):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            try:
                name, club = filename.split('-')[0], filename.split('-')[1].split('.')[0]
                image_path = f'/static/assets/candidates/{filename}'
                
                candidate = db.query(models.Candidate).filter_by(
                    name=name, 
                    club=club
                ).first()
                
                if not candidate:
                    candidate = models.Candidate(
                        name=name,
                        club=club,
                        image_path=image_path,
                        votes=0
                    )
                    db.add(candidate)
                    db.commit()
                
                candidates.append({
                    'id': candidate.id,
                    'name': name,
                    'club': club,
                    'image_path': image_path,
                    'votes': candidate.votes
                })
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")
    
    return templates.TemplateResponse(
        "index.html", 
        {"request": request, "candidates": candidates}
    )

@app.post("/vote")
async def vote(
    candidate_id: int = Form(...),
    vote_count: int = Form(1),
    db: Session = Depends(database.get_db)
):
    candidate = db.query(models.Candidate).filter(
        models.Candidate.id == candidate_id
    ).first()
    
    if candidate:
        candidate.votes += vote_count
        db.commit()
    
    return RedirectResponse(url="/", status_code=303)

@app.get("/votes")
async def view_votes(request: Request, db: Session = Depends(database.get_db)):
    candidates = db.query(models.Candidate).all()
    total_votes = sum(candidate.votes for candidate in candidates)
    
    for candidate in candidates:
        candidate.percentage = (candidate.votes / total_votes * 100) if total_votes > 0 else 0
    
    candidates = sorted(candidates, key=lambda x: x.votes, reverse=True)
    
    return templates.TemplateResponse(
        "votes.html",
        {
            "request": request,
            "candidates": candidates,
            "total_votes": total_votes
        }
    )

@app.post("/initiate-payment")
async def initiate_payment(
    request: Request,
    candidate_id: int = Form(...),
    vote_count: int = Form(...),
    email: str = Form(...),
    db: Session = Depends(database.get_db)
):
    try:
        # Validate inputs
        if vote_count < 1:
            raise HTTPException(status_code=400, detail="Vote count must be at least 1")

        # Check if candidate exists
        candidate = db.query(models.Candidate).filter(models.Candidate.id == candidate_id).first()
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")

        # Calculate amount in kobo (50 Naira per vote)
        amount = vote_count * 50 * 100  # Convert to kobo

        # Generate reference
        reference = f"vote_{secrets.token_urlsafe(8)}"

        # Create transaction record
        transaction = models.Transaction(
            reference=reference,
            candidate_id=candidate_id,
            vote_count=vote_count,
            amount=amount/100,  # Store in Naira
            email=email,
            status="pending"
        )
        db.add(transaction)
        db.commit()

        # Initialize Paystack payment
        headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "email": email,
            "amount": amount,
            "reference": reference,
            "callback_url": f"{settings.BASE_URL}/verify-payment",
            "metadata": {
                "candidate_id": candidate_id,
                "vote_count": vote_count
            }
        }

        response = requests.post(
            "https://api.paystack.co/transaction/initialize",
            headers=headers,
            json=payload
        )

        if response.status_code == 200:
            data = response.json()
            if data["status"]:
                return JSONResponse({
                    "status": "success",
                    "authorization_url": data["data"]["authorization_url"]
                })

        db.rollback()
        raise HTTPException(status_code=400, detail="Payment initialization failed")

    except Exception as e:
        db.rollback()
        print(f"General error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/verify-payment")
async def verify_payment(
    reference: str,
    db: Session = Depends(database.get_db)
):
    try:
        # Get transaction record
        transaction = db.query(models.Transaction).filter(
            models.Transaction.reference == reference
        ).first()

        if not transaction:
            return RedirectResponse(
                url="/?error=invalid_transaction",
                status_code=303
            )

        # Verify with Paystack
        headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"
        }
        
        response = requests.get(
            f"https://api.paystack.co/transaction/verify/{reference}",
            headers=headers
        )

        if response.status_code == 200:
            data = response.json()
            
            if data["status"] and data["data"]["status"] == "success":
                # Update transaction status
                transaction.status = "success"
                
                # Update candidate votes
                candidate = db.query(models.Candidate).filter(
                    models.Candidate.id == transaction.candidate_id
                ).first()

                if candidate:
                    candidate.votes += transaction.vote_count
                    db.commit()
                    return RedirectResponse(
                        url=f"/?success=true&votes={transaction.vote_count}",
                        status_code=303
                    )

        # Update transaction status to failed
        transaction.status = "failed"
        db.commit()
        
        return RedirectResponse(
            url="/?error=payment_failed",
            status_code=303
        )

    except Exception as e:
        print(f"Verification error: {str(e)}")
        return RedirectResponse(
            url="/?error=verification_error",
            status_code=303
        )

@app.get("/results")
async def results(request: Request, db: Session = Depends(database.get_db)):
    # Check admin access
    if not verify_admin_cookie(request):
        return RedirectResponse(
            url="/admin/login",
            status_code=303
        )

    candidates = db.query(models.Candidate).all()
    total_votes = sum(candidate.votes for candidate in candidates)
    
    # Calculate percentages
    results_data = []
    for candidate in candidates:
        percentage = (candidate.votes / total_votes * 100) if total_votes > 0 else 0
        results_data.append({
            'name': candidate.name,
            'club': candidate.club,
            'votes': candidate.votes,
            'percentage': round(percentage, 1)
        })
    
    # Sort by votes (highest first)
    results_data.sort(key=lambda x: x['votes'], reverse=True)
    
    return templates.TemplateResponse(
        "results.html",
        {
            "request": request,
            "candidates": results_data,
            "total_votes": total_votes
        }
    )

@app.get("/admin/login")
async def admin_login(request: Request):
    return templates.TemplateResponse(
        "admin_login.html",
        {"request": request, "error": None}
    )

@app.post("/admin/login")
async def admin_login_post(
    request: Request,
    response: Response,
    password: str = Form(...)
):
    if password == settings.ADMIN_PASSWORD:
        response = RedirectResponse(
            url="/results",
            status_code=303
        )
        set_admin_cookie(response, f"admin_{password}")
        return response
    
    return templates.TemplateResponse(
        "admin_login.html",
        {
            "request": request,
            "error": "Invalid password"
        }
    )

@app.get("/admin/logout")
async def admin_logout():
    response = RedirectResponse(
        url="/",
        status_code=303
    )
    response.delete_cookie("admin_access")
    return response

@app.middleware("http")
async def catch_exceptions_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )