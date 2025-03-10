from functools import wraps
import logging
from typing import Dict, List, Optional
from urllib.parse import parse_qs, urlparse
from fastapi import Depends, Request, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

from src.core.settings import settings
from src.core.exceptions import ForbiddenException,NotFoundException,UnauthorizedException
from src.models.role import RoleEnum
from src.core.security import JWTHandler

class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super(JWTBearer, self).__call__(request)
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(status_code=403, detail="Invalid authentication scheme.")
            if not self.verify_jwt(credentials.credentials):
                raise HTTPException(status_code=403, detail="Invalid token or expired token.")
            return credentials.credentials
        else:
            raise HTTPException(status_code=403, detail="Invalid authorization code.")

    def verify_jwt(self, jwtoken: str) -> bool:
        isTokenValid: bool = False

        try:
            payload = JWTHandler.decode(jwtoken)
        except:
            payload = None
        if payload:
            isTokenValid = True

        return isTokenValid
    
def get_current_user(request:Request, token:str = Depends(JWTBearer())):
    try:
        user_payload = JWTHandler.decode(token)
        return user_payload
    except Exception as e:
        raise HTTPException(status_code=403, detail="Invalid token or expired token")

from functools import wraps
from typing import List, Callable
from fastapi import HTTPException, Request
from src.models.role import RoleEnum

def require_roles(allowed_roles: List[str]):
    """
    Decorator to check if the current user has required roles to access the endpoint.
    
    Args:
        allowed_roles (List[str]): List of role names that are allowed to access the endpoint
        
    Returns:
        Callable: Decorated function that checks user roles before executing the endpoint
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request: Request = kwargs.get('request')
            current_user: dict = kwargs.get('current_user')
            
            if not current_user:
                raise UnauthorizedException(
                    message="User not authenticated"
                )
            
            user_role = current_user.get('role')
            if not user_role:
                raise NotFoundException(message='User not found')
                
            if user_role not in allowed_roles:
                raise ForbiddenException(
                    message=f"Access denied. Required roles: {', '.join(allowed_roles)}"
                )
                
            return await func(*args, **kwargs)
        return wrapper
    return decorator




logger = logging.getLogger(__name__)


class JWTBearerWebSocket:
    def __init__(self, auto_error: bool = True):
        self.auto_error = auto_error

    async def __call__(self, websocket: WebSocket) -> Optional[str]:
        try:
            query_params = websocket.query_params
            token = query_params.get("token")
            
            if not token:
                logger.info("Not token")
                raise HTTPException(status_code=403, detail="Token is required in query parameters")

            # Проверка токена
            if not self.verify_jwt(token):
                logger.info("Invalid or expired token")
                raise HTTPException(status_code=403, detail="Invalid or expired token")
            
            return token
        except Exception as e:
            logger.error(f"Error in JWT bearer authentication: {str(e)}")
            raise HTTPException(status_code=403, detail="Authorization token required")

    def verify_jwt(self, jwtoken: str) -> bool:
        try:
            payload = JWTHandler.decode(jwtoken)
            return payload is not None
        except Exception as e:
            logger.error(f"JWT verification error: {str(e)}")
            return False
        

async def get_current_user_ws(token: str = Depends(JWTBearerWebSocket())) -> Dict:
    try:
        user_payload = JWTHandler.decode(token)
        if user_payload:
            return user_payload  
        else:
            raise HTTPException(status_code=403, detail="Invalid or expired token")
    except Exception as e:
        logger.error(f"Error decoding token: {str(e)}")
        raise HTTPException(status_code=403, detail="Invalid or expired token")