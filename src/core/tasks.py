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

# Configure Celery beat schedule
celery_app.conf.enable_utc = True
celery_app.conf.beat_schedule = {
    'process-expired-free-trials': {
        'task': 'tasks.process_expired_free_trials',
        'schedule': crontab(hour=0, minute=0),  # Run daily at midnight
    },
}


@celery_app.task
def process_expired_free_trials():
    logger.info("Starting expired free trial processing for all balances...")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(_process_expired_free_trials())


async def _process_expired_free_trials():
    try:
        postgres = session_manager
        one_day_ago = datetime.utcnow() - timedelta(days=1)
        processed_count = 0

        async with postgres.session() as session:
            async with session.begin():
                query = select(Balance).where(
                    and_(
                        Balance.free_trial.is_(True),
                        Balance.created_at <= one_day_ago
                    )
                )
                result = await session.execute(query)
                expired_trials = result.scalars().all()

                balance_repo = BalanceRepository(session)

                for balance in expired_trials:
                    logger.info(
                        "Processing expired trial for organization_id: %s",
                        balance.organization_id
                    )

                    await _apply_expired_trial_logic(balance_repo, balance)
                    processed_count += 1
                    await session.flush()

                logger.info("Processed %d expired free trials.", processed_count)
                return {"processed": processed_count}
    except Exception as exc:
        logger.error("Error processing expired free trials: %s", str(exc))
        raise


@shared_task
def free_trial_tracker(balance_id):
    logger.info("Starting expired free trial processing for balance_id=%s", balance_id)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(_process_single_free_trial(balance_id))


async def _process_single_free_trial(balance_id):
    try:
        postgres = session_manager

        async with postgres.session() as session:
            async with session.begin():
                query = select(Balance).where(Balance.id == balance_id)
                result = await session.execute(query)
                balance = result.scalar_one_or_none()

                if not balance:
                    logger.info("No balance found with id=%s", balance_id)
                    return

                balance_repo = BalanceRepository(session)
                await _apply_expired_trial_logic(balance_repo, balance)
                await session.flush()
    except Exception as exc:
        logger.error("Error processing expired trial for balance_id=%s: %s", balance_id, str(exc))
        raise


async def _apply_expired_trial_logic(balance_repo: BalanceRepository, balance: Balance):
    if balance.atl_tokens >= 15:
        await balance_repo.withdraw_balance(balance.organization_id, 15)
        logger.info("Reduced unused trial balance by 15 tokens.")
    else:
        await balance_repo.update_balance(balance.organization_id, {"atl_tokens": 0})
        logger.info("Set partially used trial balance to 0 tokens.")

    await balance_repo.update_balance(balance.organization_id, {"free_trial": False})
