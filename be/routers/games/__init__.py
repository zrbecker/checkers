from fastapi import APIRouter
from .create import router as create_router
from .read import router as read_router
from .join import router as join_router
from .move import router as move_router
from .ai_move import router as ai_move_router
from .resign import router as resign_router
from .draw import router as draw_router

router = APIRouter(tags=["games"])

router.include_router(create_router, prefix="/games")
router.include_router(read_router, prefix="/games")
router.include_router(join_router, prefix="/games")
router.include_router(move_router, prefix="/games")
router.include_router(ai_move_router, prefix="/games")
router.include_router(resign_router, prefix="/games")
router.include_router(draw_router, prefix="/games")
