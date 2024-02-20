from flask import Blueprint, jsonify, request
from app.model import Location, db
from sqlalchemy import or_
from flask_cors import CORS

location_routes = Blueprint('locations', __name__)
CORS(location_routes, resources={r"/*": {"origins": "*"}})

@location_routes.route('/', methods=['GET'])
def get_locations():
  query = request.args.get('query')

  if query:
    locations = Location.query.filter(
      or_(
        Location.Name.ilike(f'%{query}%'),
      )
    ).all()
  else:
    locations = Location.query.all()

  formatted_locations = [location.to_dict() for location in locations]
  return jsonify({'locations':formatted_locations})

@location_routes.route('/<location_id>', methods=['GET'])
def get_location_by_id(location_id):
  location = Location.query.filter_by(LocationID=location_id).first()

  if location:
    formatted_location = location.to_dict()
    return jsonify({'location':formatted_location})
  else:
    return jsonify({'message': 'Location not found'}), 404
  
@location_routes.route('/create', methods=['POST'])
def create_location():
  data = request.get_json()

  if 'Name' not in data or 'Address' not in data or 'Capacity' not in data:
      return jsonify({'message': 'Missing required fields'}), 400

  new_location = Location(
      Name=data['Name'],
      Address=data['Address'],
      Capacity=data['Capacity'],
  )

  db.session.add(new_location)
  db.session.commit()

  return jsonify(new_location.to_dict()), 201

@location_routes.route('/update', methods=['PUT'])
def update_location():
    data = request.get_json()

    if 'LocationID' not in data:
        return jsonify({'message': 'LocationID is required'}), 400

    location_id = data['LocationID']
    location = Location.query.get(location_id)

    if not location:
        return jsonify({'message': 'Location not found'}), 404

    # Update location attributes if they exist in the request data
    if 'Name' in data:
        location.Name = data['Name']
    if 'Address' in data:
        location.Address = data['Address']
    if 'Capacity' in data:
        location.Capacity = data['Capacity']

    db.session.commit()

    return jsonify(location.to_dict()), 200

@location_routes.route('/<location_id>', methods=['DELETE'])
def delete_location(location_id):
  location = Location.query.get(location_id)

  if not location:
      return jsonify({'message': 'Location not found'}), 404

  db.session.delete(location)
  db.session.commit()

  return jsonify({'message': 'Location deleted successfully'}), 200