from flask import Blueprint, jsonify, request
from app.model import Event, Location,db
from sqlalchemy import or_

event_routes = Blueprint('events', __name__)

@event_routes.route('/events', methods=['GET'])
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

  formatted_events = {str(event.EventID): event.to_dict() for event in events}
  return jsonify(formatted_events)

@event_routes.route('/events/<event_id>', methods=['GET'])
def get_event_by_id(event_id):
  event = Event.query.filter_by(EventID=event_id).first()

  if event:
    formatted_event = event.to_dict()
    return jsonify(formatted_event)
  else:
    return jsonify({'message': 'Event not found'}), 404

@event_routes.route('/events/host', methods=['POST'])
def create_event():
    data = request.get_json()

    if 'Name' not in data or 'DateTime' not in data or 'LocationID' not in data or 'OrganizerID' not in data:
        return jsonify({'message': 'Missing required fields'}), 400

    new_event = Event(
        Name=data['Name'],
        Description=data.get('Description'),
        DateTime=data['DateTime'],
        EndTime=data.get('EndTime'),
        LocationID=data['LocationID'],
        OrganizerID=data['OrganizerID'],
        image_url=data.get('image_url')
    )

    db.session.add(new_event)
    db.session.commit()

    return jsonify(new_event.to_dict()), 201

@event_routes.route('events/<event_id>', methods=['DELETE'])
def delete_event(event_id):
    event = Event.query.filter_by(EventID=event_id).first()

    if event:
        db.session.delete(event)
        db.session.commit()
        return jsonify({'message': 'Event deleted'}), 200
    else:
        return jsonify({'message': 'Event not found'}), 404