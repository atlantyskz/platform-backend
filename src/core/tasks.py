import asyncio
import logging
from datetime import datetime, timedelta

from celery import shared_task
from celery.schedules import crontab
from sqlalchemy import and_
from sqlalchemy.future import select

from src.core.celery_config import celery_app
from src.core.databases import session_manager
from src.models.balance import Balance
from src.repositories.balance import BalanceRepository

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Celery to use UTC timezone

# Define the periodic tasks (like cron jobs)
celery_app.conf.enable_utc = True

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
    """Process all free trials that have expired (older than 1 days)."""
    logger.info("Starting expired free trial processing")

    # Run the async function using asyncio
    return asyncio.run(_process_expired_free_trials_async())


async def _process_expired_free_trials_async():
    """Async implementation to process expired free trials."""
    try:
        postgres = session_manager
        one_day_ago = datetime.utcnow() - timedelta(days=1)
        processed_count = 0

        async with postgres.session() as session:
            async with session.begin():
                # Find balances with active free trials created more than 1 days ago
                query = select(Balance).where(
                    and_(
                        Balance.free_trial == True,
                        Balance.created_at <= one_day_ago
                    )
                )

                result = await session.execute(query)
                expired_trials = result.scalars().all()
                balance_repo = BalanceRepository(session)

                for balance in expired_trials:
                    logger.info(f"Processing expired trial for organization_id: {balance.organization_id}")
                    # Apply the business logic:
                    if balance.atl_tokens >= 10000:
                        await balance_repo.withdraw_balance(balance.organization_id, 9990)
                        logger.info(f"Reduced unused trial balance from 100 to 10 tokens")

                    elif balance.atl_tokens < 10000:
                        await balance_repo.update_balance(balance.organization_id, data={"atl_tokens": 10})
                        logger.info(f"Set partially used trial balance to 10 tokens")

                    await balance_repo.update_balance(balance.organization_id, data={"free_trial": False})

                    processed_count += 1
                    await session.flush()
                logger.info(f"Processed {processed_count} expired free trials")
                return {"processed": processed_count}
    except Exception as e:
        logger.error(f"Error processing expired trials: {str(e)}")
        raise



@shared_task
def free_trial_tracker(balance_id):
    """Process all free trials that have expired (older than 3 days)."""
    logger.info("Starting expired free trial processing")

    # Run the async function using asyncio
    return asyncio.run(_process_expired_free_trials_async(balance_id))


async def _process_expired_free_trials_async(balance_id):
    try:
        postgres = session_manager

        async with postgres.session() as session:
            async with session.begin():
                query = select(Balance).where(
                    and_(
                        Balance.id == balance_id,
                    )
                )

                result = await session.execute(query)
                balance = result.scalar_one_or_none()

                balance_repo = BalanceRepository(session)

                if balance.atl_tokens >= 10000:
                    await balance_repo.withdraw_balance(balance.organization_id, 9990)

                elif balance.atl_tokens < 10000:
                    await balance_repo.update_balance(balance.organization_id, data={"atl_tokens": 10})

                await balance_repo.update_balance(balance.organization_id, data={"free_trial": False})
                await session.flush()
    except Exception as e:
        logger.error(f"Error processing expired trials: {str(e)}")
        raise
