from app import app, db, Reward

def add_sample_rewards():
    with app.app_context():
        # Sample rewards
        rewards = [
            {
                'name': 'Descuento de $200',
                'description': 'Obtén $200 pesos de descuento en tu próxima compra',
                'points_required': 100,
                'available': True
            },
            {
                'name': 'Envío Gratis',
                'description': 'Envío gratis en tu próximo pedido, sin monto mínimo',
                'points_required': 150,
                'available': True
            },
            {
                'name': 'Regalo Sorpresa',
                'description': 'Recibe un regalo sorpresa especial en tu próxima compra',
                'points_required': 200,
                'available': True
            },
            {
                'name': 'Descuento Premium',
                'description': 'Obtén un 25% de descuento en tu próxima compra',
                'points_required': 250,
                'available': True
            }
        ]

        # Delete existing rewards
        Reward.query.delete()
        
        # Add new rewards
        for reward_data in rewards:
            reward = Reward(**reward_data)
            db.session.add(reward)

        db.session.commit()
        print("Sample rewards added successfully!")

if __name__ == '__main__':
    add_sample_rewards()
