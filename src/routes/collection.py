from fastapi import APIRouter


router = APIRouter(tags=['Collection'], prefix='/collection')


@router.get("/")
def collection_home():
    return {'message': 'Welcome to collections'}
