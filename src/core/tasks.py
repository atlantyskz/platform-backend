# tasks.py
import asyncio
import logging
from celery import Celery
from celery.schedules import crontab
from sqlalchemy.future import select
from sqlalchemy import and_
from datetime import datetime, timedelta

from src.models.balance import Balance
from src.core.databases import session_manager
from src.core.celery_config import celery_app
# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Configure Celery to use UTC timezone
celery_app.conf.enable_utc = True

# Define the periodic tasks (like cron jobs)
celery_app.conf.beat_schedule = {
    'process-expired-free-trials': {
        'task': 'tasks.process_expired_free_trials',
        'schedule': crontab(hour=0, minute=0),  # Run daily at midnight
        # For testing, you might want to run more frequently
        # 'schedule': 60.0,  # Run every 60 seconds
    },
}

@celery_app.task
def process_expired_free_trials():
    """Process all free trials that have expired (older than 3 days)."""
    logger.info("Starting expired free trial processing")
    
    # Run the async function using asyncio
    return asyncio.run(_process_expired_free_trials_async())

async def _process_expired_free_trials_async():
    """Async implementation to process expired free trials."""
    try:
        postgres = session_manager
        three_days_ago = datetime.utcnow() - timedelta(days=3)
        processed_count = 0
        
        async with postgres.session() as session:
            async with session.begin():
                # Find balances with active free trials created more than 3 days ago
                query = select(Balance).where(
                    and_(
                        Balance.free_trial == True,
                        Balance.created_at <= three_days_ago
                    )
                )
                
                result = await session.execute(query)
                expired_trials = result.scalars().all()
                
                for balance in expired_trials:
                    logger.info(f"Processing expired trial for organization_id: {balance.organization_id}")
                    
                    # Apply the business logic:
                    if balance.atl_tokens == 100:
                        # Unused trial - subtract 90 tokens
                        balance.atl_tokens -= 90
                        logger.info(f"Reduced unused trial balance from 100 to 10 tokens")
                    elif balance.atl_tokens < 100:
                        # Partially used trial - set to 10 tokens
                        balance.atl_tokens = 10
                        logger.info(f"Set partially used trial balance to 10 tokens")
                    else:
                        # More than 100 tokens - subtract 90 tokens
                        balance.atl_tokens -= 90
                        logger.info(f"Reduced balance from {balance.atl_tokens + 90} to {balance.atl_tokens} tokens")
                    
                    # Mark free trial as expired
                    balance.free_trial = False
                    processed_count += 1
                
                logger.info(f"Processed {processed_count} expired free trials")
                return {"processed": processed_count}
    except Exception as e:
        logger.error(f"Error processing expired trials: {str(e)}")
        raise