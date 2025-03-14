from app import app, db, Reward, User, Transaction
from werkzeug.security import generate_password_hash

def setup_test_data():
    with app.app_context():
        # Create test rewards
        rewards = [
            Reward(
                name='Descuento 10%',
                description='10% de descuento en tu próxima compra',
                points_required=1000,
                available=True
            ),
            Reward(
                name='Producto Gratis',
                description='Un producto gratis de nuestra selección',
                points_required=2000,
                available=True
            ),
            Reward(
                name='Servicio Premium',
                description='Un mes de servicio premium gratuito',
                points_required=3000,
                available=True
            )
        ]
        
        for reward in rewards:
            db.session.add(reward)
        
        # Create a test user with some points
        test_user = User(
            name='Cliente Prueba',
            email='cliente@test.com',
            phone='1234567890',
            password=generate_password_hash('test123'),
            points=500
        )
        db.session.add(test_user)
        
        # Add some test transactions
        transactions = [
            Transaction(
                user_id=1,  # This will be the admin user
                amount=1000.0,
                points_earned=50
            ),
            Transaction(
                user_id=1,
                amount=2000.0,
                points_earned=100
            )
        ]
        
        for transaction in transactions:
            db.session.add(transaction)
            
        db.session.commit()
        print("Test data has been created successfully!")

if __name__ == '__main__':
    setup_test_data()
