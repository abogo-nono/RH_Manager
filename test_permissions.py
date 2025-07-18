import sys
from app import create_app

def test_routes():
    app = create_app()
    client = app.test_client()
    with app.app_context():
        try:
            # Login as admin
            resp = client.post('/login', data={'nom_utilisateur': 'admin', 'mot_de_passe': 'admin123'}, follow_redirects=True)
            print('Login status:', resp.status_code)
            sys.stdout.flush()
            # Test /evaluations
            eval_resp = client.get('/evaluations')
            print('Evaluations:', eval_resp.status_code)
            sys.stdout.flush()
            paie_resp = client.get('/paie')
            print('Paie:', paie_resp.status_code)
            sys.stdout.flush()
        except Exception as e:
            print('Error:', e)
            sys.stdout.flush()

if __name__ == "__main__":
    test_routes()
