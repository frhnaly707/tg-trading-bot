from app.handlers.analyze_auto import router as analyze_router
from app.handlers.common import router as common_router

all_routers = [common_router, analyze_router]
