from enum import Enum
from functools import wraps
from typing import TypeVar, Callable, Any, Optional, Type
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.exceptions import CustomException

T = TypeVar('T')

class TransactionStrategy(Enum):
    REQUIRED = "REQUIRED"
    REQUIRES_NEW = "REQUIRES_NEW"
    NESTED = "NESTED"

class TransactionContext:

    def __init__(self, session: AsyncSession, strategy: TransactionStrategy):
        self.session = session
        self.strategy = strategy
        self._activate_transaction = None
        self._savepoint = None

    async def __aenter__(self):
        if self.strategy == TransactionStrategy.REQUIRED:
            if self.session.in_transaction():
                self._activate_transaction = False 
            else:
                await self.session.begin() 
                self._activate_transaction = True
        elif self.strategy == TransactionStrategy.REQUIRES_NEW:
            await self.session.begin()  
            self._activate_transaction = True
        elif self.strategy == TransactionStrategy.NESTED:
            await self.session.begin_nested() 
            self._activate_transaction = True
        
        return self    
    
    async def __aexit__(self, exc_type, exc_val, ext_tb):
        if exc_type is not None:
            if self._activate_transaction:
                await self.session.rollback() 
            return False
        
        if self._activate_transaction:
            await self.session.commit()  
        return True

class TransactionManager:

    def __init__(self,session: AsyncSession):
        self.session = session
        self._context_stack = []
    
    def transaction(
        self,
        strategy:TransactionStrategy = TransactionStrategy.REQUIRED,
        error_handler: Optional[Callable[[Exception],Any]] = Any
    )->Callable:
        
        def decorator(func: Callable[..., T])->Callable[...,T]:
            @wraps(func)
            async def wrapper(*args:Any,**kwargs:Any)->T:
                async with TransactionContext(self.session,strategy) as ctx:
                    try:
                        result = await func(*args,**kwargs)
                        return result
                    except Exception as e:
                        if error_handler:
                            return await error_handler(e)
                        raise CustomException(message="Database Transaction Error")
            return wrapper
        return decorator


class TransactionalMixin:

    def __init__(self,session:AsyncSession):
        self._transaction_manager = TransactionManager(session)

    @staticmethod
    def transactional(self, strategy: TransactionStrategy = TransactionStrategy.REQUIRED):
        return self._transaction_manager.transaction(strategy)