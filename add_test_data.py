from app import app, db, User, Transaction, Reward
from datetime import datetime, timedelta

def add_test_data():
    with app.app_context():
        # Get our test user
        user = User.query.filter_by(email='test@example.com').first()
        if not user:
            print("Test user not found!")
            return

        # Add some sample transactions
        transactions = [
            Transaction(
                user_id=user.id,
                amount=1000.00,
                points_earned=50,
                date=datetime.now() - timedelta(days=5)
            ),
            Transaction(
                user_id=user.id,
                amount=500.00,
                points_earned=25,
                date=datetime.now() - timedelta(days=3)
            ),
            Transaction(
                user_id=user.id,
                amount=2000.00,
                points_earned=100,
                date=datetime.now() - timedelta(days=1)
            )
        ]
        
        # Add some sample rewards
        rewards = [
            Reward(
                name="Descuento de $100",
                description="Obtén $100 pesos de descuento en tu próxima compra",
                points_required=200,
                available=True
            ),
            Reward(
                name="Envío Gratis",
                description="Envío gratis en tu próximo pedido",
                points_required=150,
                available=True
            ),
            Reward(
                name="Regalo Sorpresa",
                description="Recibe un regalo sorpresa en tu próxima compra",
                points_required=300,
                available=True
            )
        ]

        # Add all to database
        db.session.add_all(transactions)
        db.session.add_all(rewards)
        
        # Update user's points
        user.points = sum(t.points_earned for t in transactions)
        
        # Commit changes
        db.session.commit()
        print("Test data added successfully!")

if __name__ == '__main__':
    add_test_data()
