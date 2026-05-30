from fastapi import APIRouter

from app.api.v1 import auth, domains, health, images, plans, providers, regions, secrets, servers

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(health.router, tags=["health"])
api_router.include_router(providers.router, prefix="/providers", tags=["providers"])
api_router.include_router(servers.router, prefix="/servers", tags=["servers"])
api_router.include_router(regions.router, prefix="/regions", tags=["regions"])
api_router.include_router(plans.router, prefix="/plans", tags=["plans"])
api_router.include_router(images.router, prefix="/images", tags=["images"])
api_router.include_router(secrets.router, prefix="/secrets", tags=["secrets"])
api_router.include_router(domains.router, prefix="/domains", tags=["domains"])
