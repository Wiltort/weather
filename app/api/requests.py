import sqlalchemy as sa
from flask import request, url_for, abort, jsonify
from app import db
from app.models import User, City
from app.api import bp
from app.api.auth import token_auth
from app.api.errors import bad_request


@bp.route('/cities', methods=['GET'])
@token_auth.login_required
def get_cities():
    cities = db.session.scalars(sa.select(City)).all()
    return jsonify([city.to_dict() for city in cities])