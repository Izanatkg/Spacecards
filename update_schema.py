from app import app, db, User

def update_schema():
    with app.app_context():
        try:
            # Add active column if it doesn't exist
            db.session.execute(db.text("ALTER TABLE user ADD COLUMN active BOOLEAN DEFAULT TRUE"))
            db.session.commit()
            print("Schema updated successfully!")
        except Exception as e:
            if "duplicate column" in str(e).lower():
                print("Column 'active' already exists")
            else:
                print(f"Error: {e}")
            db.session.rollback()

if __name__ == '__main__':
    update_schema()
