from app import app, db, User, Transaction, SystemConfig
from datetime import datetime, timedelta
from sqlalchemy import func

def simulate_purchases():
    with app.app_context():
        # Get the test user (case-insensitive email search)
        user = User.query.filter(func.lower(User.email) == func.lower('uliseseter@gmail.com')).first()
        if not user:
            print("Test user not found. Please register first at http://127.0.0.1:5001/register")
            return

        # Get or create system config
        config = SystemConfig.query.first()
        if not config:
            config = SystemConfig()
            config.points_rate = 5.0  # 5% in points
            config.min_amount = 100.0  # Minimum purchase amount
            db.session.add(config)
            db.session.commit()

        # Sample purchase amounts
        purchases = [
            (1500.00, datetime.now() - timedelta(days=7)),
            (800.00, datetime.now() - timedelta(days=5)),
            (2000.00, datetime.now() - timedelta(days=3)),
            (1200.00, datetime.now() - timedelta(days=1))
        ]

        # Create transactions
        for amount, date in purchases:
            points = int((amount * config.points_rate) / 100)
            transaction = Transaction(
                user_id=user.id,
                amount=amount,
                points_earned=points,
                date=date
            )
            db.session.add(transaction)
            user.points += points

        db.session.commit()
        print(f"Added {len(purchases)} transactions for user {user.email}")
        print(f"Total points: {user.points}")

if __name__ == '__main__':
    simulate_purchases()
