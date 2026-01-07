from fastapi import APIRouter, Request, HTTPException, Header
from sqlalchemy import select
from datetime import datetime, timedelta
import stripe

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.user import User, SubscriptionTier

router = APIRouter()

stripe.api_key = settings.STRIPE_SECRET_KEY

@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None),
):
    """Handle Stripe webhooks"""
    payload = await request.body()

    try:
        event = stripe.Webhook.construct_event(
            payload,
            stripe_signature,
            settings.STRIPE_WEBHOOK_SECRET,
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle events
    if event['type'] == 'checkout.session.completed':
        await handle_checkout_completed(event['data']['object'])

    elif event['type'] == 'customer.subscription.updated':
        await handle_subscription_updated(event['data']['object'])

    elif event['type'] == 'customer.subscription.deleted':
        await handle_subscription_deleted(event['data']['object'])

    elif event['type'] == 'invoice.payment_failed':
        await handle_payment_failed(event['data']['object'])

    return {"status": "ok"}

async def handle_checkout_completed(session: dict):
    """Handle successful checkout"""
    customer_id = session.get('customer')
    subscription_id = session.get('subscription')

    if not customer_id:
        return

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.stripe_customer_id == customer_id)
        )
        user = result.scalar_one_or_none()

        if user:
            # Get subscription details from Stripe
            subscription = stripe.Subscription.retrieve(subscription_id)

            # Determine tier from price
            price_id = subscription['items']['data'][0]['price']['id']
            tier = get_tier_from_price(price_id)

            user.subscription_tier = tier
            user.subscription_expires_at = datetime.fromtimestamp(
                subscription['current_period_end']
            )

            await db.commit()

async def handle_subscription_updated(subscription: dict):
    """Handle subscription update"""
    customer_id = subscription.get('customer')

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.stripe_customer_id == customer_id)
        )
        user = result.scalar_one_or_none()

        if user:
            if subscription['status'] == 'active':
                price_id = subscription['items']['data'][0]['price']['id']
                user.subscription_tier = get_tier_from_price(price_id)
                user.subscription_expires_at = datetime.fromtimestamp(
                    subscription['current_period_end']
                )
            elif subscription['status'] in ('canceled', 'unpaid'):
                user.subscription_tier = SubscriptionTier.FREE
                user.subscription_expires_at = None

            await db.commit()

async def handle_subscription_deleted(subscription: dict):
    """Handle subscription cancellation"""
    customer_id = subscription.get('customer')

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.stripe_customer_id == customer_id)
        )
        user = result.scalar_one_or_none()

        if user:
            user.subscription_tier = SubscriptionTier.FREE
            user.subscription_expires_at = None
            await db.commit()

async def handle_payment_failed(invoice: dict):
    """Handle failed payment"""
    customer_id = invoice.get('customer')

    # Could send notification to user, etc.
    pass

def get_tier_from_price(price_id: str) -> SubscriptionTier:
    """Map Stripe price ID to subscription tier"""
    # Configure these in your Stripe dashboard
    price_mapping = {
        'price_pro_monthly': SubscriptionTier.PRO,
        'price_pro_yearly': SubscriptionTier.PRO,
        'price_ultra_monthly': SubscriptionTier.ULTRA,
        'price_ultra_yearly': SubscriptionTier.ULTRA,
    }
    return price_mapping.get(price_id, SubscriptionTier.PRO)

# Create checkout session endpoint
@router.post("/create-checkout")
async def create_checkout_session(
    price_id: str,
    user_id: int,
):
    """Create Stripe checkout session"""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Create or get Stripe customer
        if not user.stripe_customer_id:
            customer = stripe.Customer.create(
                email=user.email,
                metadata={'user_id': str(user.id)},
            )
            user.stripe_customer_id = customer.id
            await db.commit()

        # Create checkout session
        session = stripe.checkout.Session.create(
            customer=user.stripe_customer_id,
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url='https://yourapp.com/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url='https://yourapp.com/cancel',
        )

        return {'checkout_url': session.url}
