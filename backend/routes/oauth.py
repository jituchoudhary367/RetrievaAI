from fastapi import APIRouter, Request, Depends, HTTPException, status
from authlib.integrations.starlette_client import OAuth, OAuthError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import RedirectResponse

from app.config import settings
from db.engine import get_db
from app.models import AuthResponse
from services.auth_service import login_or_create_oauth_user

router = APIRouter(tags=["OAuth"])

oauth = OAuth()

if settings.oauth.google_client_id:
    oauth.register(
        name='google',
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_id=settings.oauth.google_client_id,
        client_secret=settings.oauth.google_client_secret,
        client_kwargs={
            'scope': 'openid email profile',
            'timeout': 30.0
        }
    )


@router.get("/{provider}/login")
async def oauth_login(provider: str, request: Request):
    client = oauth.create_client(provider)
    if not client:
        raise HTTPException(status_code=404, detail=f"Provider {provider} not configured")
    
    # The callback URI needs to point back to the backend securely
    redirect_uri = str(request.url_for('oauth_callback', provider=provider))
    return await client.authorize_redirect(request, redirect_uri, prompt="select_account")

@router.get("/{provider}/callback")
async def oauth_callback(provider: str, request: Request, db: AsyncSession = Depends(get_db)):
    client = oauth.create_client(provider)
    if not client:
        raise HTTPException(status_code=404, detail=f"Provider {provider} not configured")
        
    try:
        token = await client.authorize_access_token(request)
    except OAuthError as error:
        raise HTTPException(status_code=400, detail=error.error)
        
    user_info = None
    if provider == 'google':
        user_info = token.get('userinfo')


    if not user_info or not user_info.get('email'):
        raise HTTPException(status_code=400, detail="Could not retrieve email from provider")
        
    email = user_info['email']
    name = user_info.get('name') or user_info.get('login') or ""
    avatar_url = user_info.get('picture')
    
    tokens = await login_or_create_oauth_user(
        session=db,
        email=email,
        display_name=name,
        provider=provider,
        avatar_url=avatar_url
    )
    
    # Redirect to frontend to process the token
    base_url = settings.frontend_base_url.rstrip('/')
    frontend_callback = f"{base_url}/oauth/callback?token={tokens.access_token}"
    return RedirectResponse(url=frontend_callback)
