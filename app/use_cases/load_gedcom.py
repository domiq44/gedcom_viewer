# app/use_cases/load_gedcom.py
from app.session import GedcomSession

def load_gedcom(filename: str) -> GedcomSession:
    session = GedcomSession()
    session.load(filename)
    return session
