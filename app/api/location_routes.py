from flask import Blueprint, jsonify, request
from app.model import Location, db
from sqlalchemy import or_

location_routes = Blueprint('locations', __name__)

@location_routes.route('/locations', methods=['GET'])
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

  formatted_locations = {str(location.LocationID): location.to_dict() for location in locations}
  return jsonify(formatted_locations)

@location_routes.route('locations/<location_id>', methods=['GET'])
def get_location_by_id(location_id):
  location = Location.query.filter_by(LocationID=location_id).first()

  if location:
    formatted_location = location.to_dict()
    return jsonify(formatted_location)
  else:
    return jsonify({'message': 'Location not found'}), 404
  
@location_routes.route('/location/host', methods=['POST'])
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

@location_routes.route('/location/<location_id>', methods=['DELETE'])
def delete_location(location_id):
    location = Location.query.get(location_id)