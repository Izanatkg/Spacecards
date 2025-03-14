from app import app, db, User

def check_users():
    with app.app_context():
        users = User.query.all()
        print("\nRegistered Users:")
        print("-----------------")
        for user in users:
            print(f"Name: {user.name}")
            print(f"Email: {user.email}")
            print(f"Points: {user.points}")
            print(f"Is Admin: {user.is_admin}")
            print("-----------------")

if __name__ == '__main__':
    check_users()
