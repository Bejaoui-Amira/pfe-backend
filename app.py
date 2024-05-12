from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_security import Security, SQLAlchemyUserDatastore, UserMixin, RoleMixin
from flask_socketio import SocketIO, emit
from datetime import datetime

# Initialize the Flask app
app = Flask(__name__)

# Configure the app
app.config['SECRET_KEY'] = 'super-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres0@localhost/monitoring'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db = SQLAlchemy(app)


@app.route('/')
def index():
    return 'Hello, world!'


# Define the User and Role models for Flask-Security
roles_users = db.Table('roles_users',
                       db.Column('user_id', db.Integer(), db.ForeignKey('utilisateur.id')),
                       db.Column('role_id', db.Integer(), db.ForeignKey('role.id')),)


class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))


class Utilisateur(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(255), nullable=False)
    mot_de_passe = db.Column(db.String(255), nullable=False)
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('utilisateurs', lazy='dynamic'))


# Define the other models
class Dashboard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'), nullable=False)
    liste_de_dashboards = db.Column(db.Text, nullable=False)


class Alerte(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type_alerte = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    date_heure = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'), nullable=False)


class Rapport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_debut = db.Column(db.DateTime, nullable=False)
    date_fin = db.Column(db.DateTime, nullable=False)
    donnees = db.Column(db.Text, nullable=False)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'), nullable=False)


class HistoriqueProduction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    enregistrements = db.Column(db.Text, nullable=False)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'), nullable=False)


class TacheProduction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text, nullable=False)
    statut = db.Column(db.String(255), nullable=False)
    priorite = db.Column(db.Integer, nullable=False)
    dashboard_id = db.Column(db.Integer, db.ForeignKey('dashboard.id'), nullable=False)


class Produit(db.Model):
    idproduit = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    tagsrfid = db.Column(db.Text, nullable=False)


class PerformanceMachine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    machine_id = db.Column(db.String(255), nullable=False)
    temps_arret = db.Column(db.Integer, nullable=False)
    temps_fonctionnement = db.Column(db.Integer, nullable=False)
    date_heure = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class StatistiquesProduction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    sous_production = db.Column(db.Integer, nullable=False)
    surproduction = db.Column(db.Integer, nullable=False)
    production_normale = db.Column(db.Integer, nullable=False)


class TendancesAnomalies(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    anomalie = db.Column(db.String(255), nullable=False)
    nombre_occurrences = db.Column(db.Integer, nullable=False)


# Initialize Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, Utilisateur, Role)
security = Security(app, user_datastore)

# Initialize Socket.IO
socketio = SocketIO(app)


# Define the API endpoints
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    utilisateur = Utilisateur.query.filter_by(nom=data['nom']).first()
    if utilisateur and utilisateur.check_password(data['mot_de_passe']):
        return jsonify({'status': 'success', 'utilisateur_id': utilisateur.id})
    else:
        return jsonify({'status': 'error', 'message': 'Invalid credentials'})


@app.route('/api/logout', methods=['POST'])
def logout():
    # Implement logout functionality here
    pass


@app.route('/api/dashboards', methods=['GET'])
@app.route('/api/dashboards/<int:utilisateur_id>', methods=['GET'])
def get_dashboards(utilisateur_id=None):
    if utilisateur_id:
        dashboards = Dashboard.query.filter_by(utilisateur_id=utilisateur_id).all()
    else:
        dashboards = Dashboard.query.all()
    return jsonify([{'id': dashboard.id, 'utilisateur_id': dashboard.utilisateur_id, 'liste_de_dashboards': dashboard.liste_de_dashboards} for dashboard in dashboards])


@app.route('/api/dashboards', methods=['POST'])
def create_dashboard():
    data = request.get_json()
    utilisateur_id = data['utilisateur_id']
    liste_de_dashboards = data['liste_de_dashboards']
    dashboard = Dashboard(utilisateur_id=utilisateur_id, liste_de_dashboards=liste_de_dashboards)
    db.session.add(dashboard)
    db.session.commit()
    return jsonify({'status': 'success', 'id': dashboard.id})


@app.route('/api/dashboards/<int:dashboard_id>', methods=['PUT'])
def update_dashboard(dashboard_id):
    data = request.get_json()
    dashboard = Dashboard.query.get(dashboard_id)
    if dashboard:
        dashboard.utilisateur_id = data['utilisateur_id']
        dashboard.liste_de_dashboards = data['liste_de_dashboards']
        db.session.commit()
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'error', 'message': 'Dashboard not found'})


@app.route('/api/dashboards/<int:dashboard_id>', methods=['DELETE'])
def delete_dashboard(dashboard_id):
    dashboard = Dashboard.query.get(dashboard_id)
    if dashboard:
        db.session.delete(dashboard)
        db.session.commit()
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'error', 'message': 'Dashboard not found'})


@app.route('/api/alertes', methods=['GET'])
@app.route('/api/alertes/<int:utilisateur_id>', methods=['GET'])
def get_alertes(utilisateur_id=None):
    if utilisateur_id:
        alertes = Alerte.query.filter_by(utilisateur_id=utilisateur_id).all()
    else:
        alertes = Alerte.query.all()
    return jsonify([{'id': alerte.id, 'type_alerte': alerte.type_alerte, 'message': alerte.message, 'date_heure': alerte.date_heure} for alerte in alertes])


@app.route('/api/alertes', methods=['POST'])
def create_alerte():
    data = request.get_json()
    type_alerte = data['type_alerte']
    message = data['message']
    utilisateur_id = data['utilisateur_id']
    alerte = Alerte(type_alerte=type_alerte, message=message, utilisateur_id=utilisateur_id)
    db.session.add(alerte)
    db.session.commit()
    return jsonify({'status': 'success', 'id': alerte.id})


@app.route('/api/alertes/<int:alerte_id>', methods=['PUT'])
def update_alerte(alerte_id):
    data = request.get_json()
    alerte = Alerte.query.get(alerte_id)
    if alerte:
        alerte.type_alerte = data['type_alerte']
        alerte.message = data['message']
        db.session.commit()
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'error', 'message': 'Alert not found'})


@app.route('/api/alertes/<int:alerte_id>', methods=['DELETE'])
def delete_alerte(alerte_id):
    alerte = Alerte.query.get(alerte_id)
    if alerte:
        db.session.delete(alerte)
        db.session.commit()
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'error', 'message': 'Alert not found'})


@app.route('/api/produit/<int:idproduit>', methods=['GET'])
def get_produit(idproduit):
    produit = Produit.query.filter_by(idproduit=idproduit).first()
    print(produit.nom)
    if produit:
        return jsonify({'status': 'success', 'produit': f'{produit.nom}'})
    else:
        return jsonify({'status': 'success', 'produit': 'not found'})


@app.route('/api/machines', methods=['GET'])
def get_machines_performance():
    machines_performance = PerformanceMachine.query.all()
    machines_performance_json = [{
        'id': machine.id,
        'machine_id': machine.machine_id,
        'temps_arret': machine.temps_arret,
        'temps_fonctionnement': machine.temps_fonctionnement,
        'date_heure': machine.date_heure.strftime('%Y-%m-%d %H:%M:%S')
    } for machine in machines_performance]
    return jsonify(machines_performance_json)


@app.route('/api/statistiques-production', methods=['GET'])
def get_production_statistics():
    production_stats = StatistiquesProduction.query.all()
    production_stats_json = [{
        'id': stat.id,
        'date': stat.date.strftime('%Y-%m-%d'),
        'sous_production': stat.sous_production,
        'surproduction': stat.surproduction,
        'production_normale': stat.production_normale
    } for stat in production_stats]
    return jsonify(production_stats_json)


@app.route('/api/tendances-anomalies', methods=['GET'])
def get_anomaly_trends():
    anomaly_trends = TendancesAnomalies.query.all()
    anomaly_trends_json = [{
        'id': trend.id,
        'date': trend.date.strftime('%Y-%m-%d'),
        'anomalie': trend.anomalie,
        'nombre_occurrences': trend.nombre_occurrences
    } for trend in anomaly_trends]
    return jsonify(anomaly_trends_json)


# Define the Socket.IO event handlers
@socketio.on('connect')
def handle_connect():
    print('Client connected')


@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')


@socketio.on('new_data')
def handle_new_data(data):
    print('Received new data:', data)
    emit('new_data', data, broadcast=True)


if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
