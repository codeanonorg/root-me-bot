from datetime import datetime
from pydantic import BaseModel


class UserBase(BaseModel):
    id_auteur: str
    nom: str


class Challenge(BaseModel):
    id_challenge: str
    url_challenge: str


class ChallengeInfo(BaseModel):
    titre: str
    rubrique: str
    soustitre: str
    score: str
    id_rubrique: str
    url_challenge: str
    date_publication: str
    difficulte: str
    auteurs: list[UserBase]
    validations: int


class Solution(BaseModel):
    id_solution: str
    url_solution: str


class Validation(BaseModel):
    id_challenge: str
    date: datetime


class User(UserBase):
    statut: str
    score: str
    position: int
    challenges: list[Challenge]
    solutions: list[Solution]
    validations: list[Validation]
