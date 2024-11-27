# app.py

from app import app 
print(app.url_map)
# Importing the Flask app instance from `app/__init__.py`

if __name__ == '__main__':
    app.run(debug=True)
