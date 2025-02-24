Pour executer ce projet,
1 creer un environnement virtuel
python -m venv venv #sur windows

2 Activer l'environnement virtuel
venv\Scripts\activate #sur windows


3 installer les dependances
pip install -r requirements.txt

4 On va creer la base de donnees
CREATE DATABASE marketdb;

5 Alternative avec Flask-Migrate (Recommandé)
Si tu veux gérer les migrations proprement, utilise Flask-Migrate :

flask db init
flask db migrate -m "Initial migration"
flask db upgrade
