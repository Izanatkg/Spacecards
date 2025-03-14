from app import app, db, User, Transaction
from datetime import datetime
from sqlalchemy import func

def add_bonus_points():
    with app.app_context():
        # Get the user
        user = User.query.filter(func.lower(User.email) == func.lower('uliseseter@gmail.com')).first()
        if not user:
            print("Usuario no encontrado")
            return

        # Create a large purchase transaction to give 1000 points
        amount = 20000.00  # $20,000 MXN purchase to get 1000 points at 5% rate
        points = 1000
        
        transaction = Transaction(
            user_id=user.id,
            amount=amount,
            points_earned=points,
            date=datetime.now()
        )
        
        db.session.add(transaction)
        user.points += points
        db.session.commit()
        
        print(f"¡Puntos añadidos exitosamente!")
        print(f"Puntos actuales: {user.points}")

if __name__ == '__main__':
    add_bonus_points()
