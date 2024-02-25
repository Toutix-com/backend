from flask import Blueprint, jsonify, request
from app.model import Event, Location,db
from sqlalchemy import or_

event_routes = Blueprint('events', __name__)

@event_routes.route('/', methods=['GET'])
def get_events():
  query = request.args.get('query')

  if query:
    events = Event.query.filter(
      or_(
        Event.Name.ilike(f'%{query}%'),
      )
    ).all()
  else:
    events = Event.query.all()

  formatted_events = [event.to_dict() for event in events]
  return jsonify({"events":formatted_events})

@event_routes.route('/<event_id>', methods=['GET'])
def get_event_by_id(event_id):
  event = Event.query.filter_by(EventID=event_id).first()

  if event:
    formatted_event = event.to_dict()
    return jsonify({'event':formatted_event}),200
  else:
    return jsonify({'message': 'Event not found'}), 404

@event_routes.route('/create', methods=['POST'])
def create_event():
    data = request.get_json()

    if 'Name' not in data or 'DateTime' not in data or 'LocationID' not in data or 'OrganizerID' not in data:
        return jsonify({'message': 'Missing required fields'}), 400
    
    # Check if an event with the same Name, DateTime, EndTime, and LocationID already exists
    existing_event = Event.query.filter_by(Name=data['Name'], DateTime=data['DateTime'], EndTime=data.get('EndTime'), LocationID=data['LocationID']).first()
    if existing_event:
        return jsonify({'message': 'An event with the same details already exists'}), 400

    new_event = Event(
        Name=data['Name'],
        Description=data.get('Description'),
        DateTime=data['DateTime'],
        EndTime=data.get('EndTime'),
        LocationID=data['LocationID'],
        OrganizerID=data['OrganizerID'],
        image_url=data.get('image_url'),
        EntryRequirement=data.get('EntryRequirement')
    )

    db.session.add(new_event)
    db.session.commit()

    return jsonify(new_event.to_dict()), 201

@event_routes.route('/update', methods=['PUT'])
def update_event():
    data = request.get_json()

    if 'EventID' not in data:
        return jsonify({'message': 'EventID is required'}), 400

    event_id = data['EventID']
    event = Event.query.get(event_id)

    if not event:
        return jsonify({'message': 'Event not found'}), 404

    # Update event attributes if they exist in the request data
    if 'Name' in data:
        event.Name = data['Name']
    if 'Description' in data:
        event.Description = data['Description']
    if 'DateTime' in data:
        event.DateTime = data['DateTime']
    if 'EndTime' in data:
        event.EndTime = data['EndTime']
    if 'LocationID' in data:
        event.LocationID = data['LocationID']
    if 'OrganizerID' in data:
        event.OrganizerID = data['OrganizerID']
    if 'image_url' in data:
        event.image_url = data['image_url']

    db.session.commit()

    return jsonify(event.to_dict()), 200

@event_routes.route('/<event_id>', methods=['DELETE'])
def delete_event(event_id):
    event = Event.query.filter_by(EventID=event_id).first()

    if event:
        db.session.delete(event)
        db.session.commit()
        return jsonify({'message': 'Event deleted'}), 200
    else:
        return jsonify({'message': 'Event not found'}), 404