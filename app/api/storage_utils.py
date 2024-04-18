import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Spacer, SimpleDocTemplate, Frame
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER
from reportlab.platypus import Image
import qrcode
import boto3


''' ADD ERROR HANDLING IN THIS CODE, to account for the case where the QR code generation fails, PDF upload failure ..
'''
def generate_qr_code(event_id, ticket_id, user, ticket_category):
    try:
        # Create QR Code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr_data = {
            "eventId": event_id,
            "ticketId": ticket_id,
            "user": user,
            "ticketCategory": ticket_category
        }
        qr_data_json = json.dumps(qr_data)
        qr.add_data(qr_data_json)
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')

        # Convert QR code to a file-like object
        img_buffer = io.BytesIO()
        img.save(img_buffer)
        img_buffer.seek(0)

        return img_buffer
    except Exception as e:
        # Handle the error here
        print(f"Error generating QR code: {str(e)}")
        return None

def generate_ticket_pdf(qr_image_buffers, event_name, attendee_name, location, ticket_id):

    # Create a BytesIO object to store the PDF data
    pdf_buffer = io.BytesIO()

    # PDF Setup

    # PDF naming format: <event_name>_<ticket_id>_<attendee_name_with_spaces_replaced_by_underscores>.pdf
    packet  = f"{event_name}_{ticket_id}_{attendee_name.replace(' ', '_')}.pdf"
    document = SimpleDocTemplate(packet, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()

    # Adding some custom styles
    styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))
    styles.add(ParagraphStyle(name='TitleStyle', alignment=TA_CENTER, fontName='Helvetica-Bold', fontSize=16))
    styles.add(ParagraphStyle(name='ConfirmationStyle', alignment=TA_CENTER))
    styles.add(ParagraphStyle(name='NameStyle', alignment=TA_CENTER))
    styles.add(ParagraphStyle(name='NotesStyle', alignment=TA_CENTER))

    # Title
    title = Paragraph('<b>Ticket Confirmation</b>', styles['TitleStyle'])
    story.append(title)
    story.append(Spacer(1, 12))

    # Confirmation Details
    confirmation_text = f'''
    <b>Receipt No:</b> {ticket_id}<br/>
    <b>Event Name:</b> {event_name}<br/>
    <b>Date:</b> December 12, 2024<br/>
    <b>Location:</b> {location}<br/>
    '''
    confirmation_details = Paragraph(confirmation_text, styles['BodyText'])
    story.append(confirmation_details)
    story.append(Spacer(1, 12))

    # Name
    name_paragraph = Paragraph(f'<b>Name:</b> {attendee_name}', styles['BodyText'])
    story.append(name_paragraph)
    story.append(Spacer(1, 12))

    # Things to Note
    notes_text = '''
    <b>Things to Note:</b><br/>
    Please arrive 30 minutes early.<br/>
    Bring this ticket and ID for entry.<br/>
    No outside food or drinks allowed.<br/>
    '''
    notes_paragraph = Paragraph(notes_text, styles['BodyText'])
    story.append(notes_paragraph)
    story.append(Spacer(1, 12))

    # Adding the QR Codes
    for qr_image_buffer in qr_image_buffers:
        qr_image = Image(qr_image_buffer, 2*inch, 2*inch)
        story.append(qr_image)
        story.append(Spacer(1, 12))  # Add some space between QR codes

    # Build PDF
    document.build(story)

    pdf_buffer.seek(0)

    # Return the PDF data as bytes
    return pdf_buffer.read()

def upload_pdf_to_s3(bucket_name, file_name, pdf_content):
    s3 = boto3.resource('s3')
    s3.Object(bucket_name, file_name).put(Body=pdf_content)

    return f"https://s3.amazonaws.com/{bucket_name}/{file_name}"

def download_pdf_from_s3(bucket_name, file_name):
    s3 = boto3.client('s3')
    response = s3.get_object(Bucket=bucket_name, Key=file_name)
    pdf_content = response['Body'].read()
    
    return pdf_content




'''
 /////        USAGE      /////// 
# Set up S3 resource with AWS credentials and region
s3 = boto3.resource(
    's3',
    aws_access_key_id='YOUR_ACCESS_KEY_ID',
    aws_secret_access_key='YOUR_SECRET_ACCESS_KEY',
    region_name='YOUR_REGION_NAME'
)

# Define variables with specific example values
bucket_name = 'your-s3-bucket-name'
file_name = 'ticket.pdf'
event_id = 123
ticket_ids = [1, 2, 3]
user = 'John Doe'
ticket_categories = ['Category A', 'Category B', 'Category C']

# Generate QR codes
qr_image_buffers = []
for i in range(len(ticket_ids)):
    qr_image_buffer = generate_qr_code(event_id, ticket_ids[i], user, ticket_categories[i])
    qr_image_buffers.append(qr_image_buffer)

# Generate PDF with all the QR codes
event_name = 'Example Event'
attendee_name = 'John Doe'
location = 'Example Location'
pdf_content = generate_ticket_pdf(qr_image_buffers, event_name, attendee_name, location, ticket_id)

# Upload the PDF to S3
s3_object = s3.Object(bucket_name, file_name)
s3_object.put(Body=pdf_content)

# Print the download link
print(f"Your PDF is available for download at: https://s3.amazonaws.com/{bucket_name}/{file_name}")
'''