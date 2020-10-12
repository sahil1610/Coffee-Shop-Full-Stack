import json

from flask import Flask, jsonify
from flask import Response, request, abort
from flask_cors import CORS

from backend.src.auth.auth import requires_auth, AuthError
from .database.models import setup_db, Drink

app = Flask(__name__)
setup_db(app)
CORS(app, resources={r"*": {"origins": "*"}})

"""
Uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
"""
# db_drop_and_create_all()


@app.route('/drinks', methods=['GET'])
def get_all_drinks() -> Response:
    """
    Get endpoint to fetch all drinks
    :return: Json response containing drinks list and their recipes
    """
    drinks = Drink.query.order_by(Drink.id).all()

    return jsonify({
        'success': True,
        'drinks': [drink.short() for drink in drinks]
    })


@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def get_drinks_detail(payload) -> Response:
    """
    Get endpoint to fetch all a particular drink detail. A person accessing this end point should have
    "get:drinks-detail" permission
    :return: Json response containing drink details
    """
    drinks = Drink.query.order_by(Drink.id).all()

    return jsonify({
        'success': True,
        'drinks': [drink.long() for drink in drinks]
    })


@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def create_drink(payload) -> Response:
    """
    Post endpoint to create a new drink. A person should have "post:drinks" permission
    :return: Json response containing created drinks details
    """
    body = request.get_json()
    if not body:
        # posting an empty json should return a 400 error.
        abort(400, 'JSON passed is empty')
    if 'recipe' not in body.keys() or 'title' not in body.keys():
        abort(400, 'Invalid JSON, "recipe" or "title" key is not present')
    if Drink.query.filter_by(title=body['title']).first():
        abort(409, 'Drink with name ' + body['title'] + ' already exists.')

    print(body)
    req_recipe = body['recipe']
    drink = Drink()
    drink.title = body['title']
    drink.recipe = json.dumps(req_recipe)  # convert object to a string
    drink.insert()

    return jsonify({'success': True, 'drinks': [drink.long()]})


@app.route('/drinks/<int:drink_id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def patch_drink(payload, drink_id):
    """
    Patch endpoint to update drink name or recipe. A person should have "patch:drinks" permission
    :param payload:  Payload from requires_auth decorator
    :param drink_id: id of the drink to be patched
    :return: Json response containing updated drinks details
    """
    body = request.get_json()
    if not body:
        # posting an empty json should return a 400 error.
        abort(400, 'JSON passed is empty')
    title = body.get('title', None)
    recipe = body.get('recipe', None)

    drink = Drink.query.filter_by(id=drink_id).one_or_none()
    if drink is None:
        abort(404, f'No drink found with the id "{drink_id}"')

    if title is None:
        abort(400, 'JSON error, "Title" key is not present')

    drink.title = title
    if recipe is not None:
        drink.recipe = json.dumps(recipe)

    drink.update()

    return jsonify({
        'success': True,
        'drinks': [drink.long()]
    })


@app.route('/drinks/<int:drink_id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drinks(payload, drink_id):
    """
    Delete endpoint to delete drink. A person should have "delete:drinks" permission
    :param payload:  Payload from requires_auth decorator
    :param drink_id: id of the drink to be deleted
    :return: Json response containing id of the deleted drink
    """
    drink = Drink.query.filter_by(id=drink_id).one_or_none()
    if drink is None:
        abort(404, f'No drink found with the id "{drink_id}"')
    drink.delete()
    return jsonify({
        'success': True,
        'deleted': drink_id
    })


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 404,
        'message': getattr(error, 'description', 'Resource Not Found')
    }), 404


@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        'success': False,
        'error': 400,
        'message': getattr(error, 'description', 'Bad Request')
    }), 400


@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        'success': False,
        'error': 405,
        'message': getattr(error, 'description', 'Method Not Allowed')
    }), 405


@app.errorhandler(409)
def conflict(error):
    return jsonify({
        'success': False,
        'error': 409,
        'message': getattr(error, 'description', 'Resource Already Exists')
    }), 409


@app.errorhandler(AuthError)
def auth_error(error):
    return jsonify({
        "success": False,
        "error": error.status_code,
        "message": error.error['description']
    }), error.status_code
