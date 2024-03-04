from flask import Blueprint, jsonify, request
from app.model import Event, Location,db, TicketCategory
from sqlalchemy import or_
from sqlalchemy import func

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

  formatted_events = []
  for event in events:
    event_dict = event.to_dict()
    cheapest_ticket_price = db.session.query(func.min(TicketCategory.price)).filter(TicketCategory.EventID == event.EventID).scalar()
    event_dict['cheapest_ticket_price'] = cheapest_ticket_price if cheapest_ticket_price else 0
    formatted_events.append(event_dict)

    return jsonify({"events": formatted_events})

@event_routes.route('/<event_id>', methods=['GET'])
def get_event_by_id(event_id):
  event = Event.query.filter_by(EventID=event_id).first()

  if event:
    cheapest_ticket_price = db.session.query(func.min(TicketCategory.price)).filter(TicketCategory.EventID == event_id).scalar()

    if cheapest_ticket_price is None:
        cheapest_ticket_price = 0
    
    formatted_event = event.to_dict()
    formatted_event['cheapest_ticket_price'] = cheapest_ticket_price

    # Add total tickets left for each category
    ticket_categories = TicketCategory.query.filter_by(EventID=event_id).all()
    formatted_event['ticket_categories'] = []
    for category in ticket_categories:
        tickets_left = category.max_limit - category.ticket_sold
        formatted_event['ticket_categories'].append({
            'category_id': category.CategoryID,
            'category_name': category.name,
            'tickets_left': tickets_left,
            'price': category.price,
        })

    return jsonify({'event': formatted_event}), 200
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
    if 'EntryRequirement' in data:
        event.EntryRequirement = data['EntryRequirement']

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
    
@event_routes.route('/<event_id>/ticket/categories', methods=['GET'])
def get_event_ticket_categories(event_id):
    event = Event.query.filter_by(EventID=event_id).first()

    if event:
        ticket_categories = event.ticket_categories
        formatted_categories = [category.to_dict() for category in ticket_categories]
        return jsonify({'ticket_categories':formatted_categories}), 200
    else:
        return jsonify({'message': 'Event not found'}), 404
    
@event_routes.route('/<event_id>/ticket/create_categories', methods=['POST'])
def create_ticket_category(event_id):
    data = request.get_json()

    new_category = TicketCategory(
        name=data['name'],
        price=data['price'],
        max_limit=data['max_limit'],
        ticket_sold=data.get('ticket_sold', 0),  # optional, defaults to 0
        description=data.get('description'),  # optional
        EventID=event_id
    )

    db.session.add(new_category)
    db.session.commit()
    
    return jsonify(new_category.to_dict()), 201

@event_routes.route('/<int:event_id>/ticket/validate', methods=['POST'])
def validate_ticket(event_id):
    # Get the event
    event = Event.query.filter_by(EventID=event_id).first()
    data = request.json
    user_id = data.get('user_id')
    ticket_category_id = data.get('ticket_category_id')
    number_of_tickets = data.get('number_of_tickets')

    user = User.query.get(user_id)
    ticket_category = TicketCategory.query.get(ticket_category_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    total_purchased_by_user = Ticket.query.filter_by(UserID=user_id, EventID=event_id).count()
    # Modify to use a variable later
    is_eligible_to_purchase = True
    if total_purchased_by_user + number_of_tickets > 4:
        is_eligible_to_purchase = False

    price = TicketCategory.query.get(ticket_category_id).price
    total = price * number_of_tickets
    service = total * 0.1

    tickets_left = ticket_category.max_limit - ticket_category.ticket_sold
    if tickets_left < number_of_tickets:
        is_eligible_to_purchase = False

    return jsonify({
        'is_eligible_to_purchase': is_eligible_to_purchase,
        'total': total,
        'service': service,
    }), 200
