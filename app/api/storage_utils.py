import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.platypus import Image
import qrcode
import boto3
import os
import json


''' ADD ERROR HANDLING IN THIS CODE, to account for the case where the QR code generation fails, PDF upload failure ..
'''
def generate_qr_code(event_name, ticket_id, user, ticket_category):
    try:
        # Create QR Code
        print('Generating QR code...')
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr_data = {
            "eventName": event_name,
            "ticketId": str(ticket_id),
            "user": user.FirstName + " " + user.LastName,
            "ticketCategory": ticket_category
        }
        print('QR data: ', qr_data)
        qr_data_json = json.dumps(qr_data)
        qr.add_data(qr_data_json)
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')

        print('QR code generated successfully')
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
    print('Generating PDF...')
    pdf_buffer = io.BytesIO()

    # PDF Setup
    pdf_name = f"{event_name}_{ticket_id}_{attendee_name.replace(' ', '_')}.pdf"
    document = SimpleDocTemplate(pdf_buffer, pagesize=letter, title=pdf_name)
    story = []
    styles = getSampleStyleSheet()

    # Custom styles
    custom_style = styles['BodyText']
    custom_style.alignment = TA_JUSTIFY

    title_style = ParagraphStyle('TitleStyle', parent=styles['Title'], fontName='Helvetica-Bold', fontSize=18, spaceAfter=12, alignment=TA_CENTER)
    header_style = ParagraphStyle('HeaderStyle', parent=styles['Heading2'], fontSize=12, spaceAfter=6, alignment=TA_CENTER)

    # Title
    title = Paragraph(f'<b>Ticket Confirmation for {event_name}</b>', title_style)
    story.append(title)

    # Confirmation Details Table
    details_data = [
        ['Receipt No:', ticket_id],
        ['Event Name:', event_name],
        ['Date:', 'December 12, 2024'],
        ['Location:', location],
        ['Attendee:', attendee_name]
    ]
    details_table = Table(details_data, colWidths=[2*inch, 4*inch])
    details_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), '#dddddd'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(details_table)
    story.append(Spacer(1, 12))

    # Things to Note
    notes_text = '''
    <b>Things to Note:</b><br/>
    Please arrive 30 minutes early.<br/>
    Bring this ticket and ID for entry.<br/>
    No outside food or drinks allowed.
    '''
    notes_paragraph = Paragraph(notes_text, custom_style)
    story.append(notes_paragraph)
    story.append(Spacer(1, 12))
    
    print('QR image buffers: ', qr_image_buffers)
    # Adding the QR Codes
    if qr_image_buffers:
        qr_table_data = [[Image(qr_image_buffer, 2*inch, 2*inch) for qr_image_buffer in qr_image_buffers]]
        qr_table = Table(qr_table_data)
        qr_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        story.append(qr_table)

    # Build PDF
    document.build(story)

    pdf_buffer.seek(0)

    # Return the PDF data as bytes
    print('PDF generated successfully')
    return pdf_buffer.getvalue()

def upload_to_s3(file_name, bucket, object_name=None):
    """
    Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified, file_name is used
    :return: True if file was uploaded, else False
    """
    print('Connecting to S3...')
    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = file_name

    # Initialize a session using your credentials
    session = boto3.Session(
        aws_access_key_id= os.getenv('aws_access_key_id'),
        aws_secret_access_key= os.getenv('aws_secret_access_key'),
        region_name='eu-west-2'
    )
    
    # Initialize S3 client
    s3_client = session.client('s3')

    print('Uploading to S3...')
    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
        print("File uploaded successfully")
        return jsonify({"message": "File uploaded successfully"}), 200
    except FileNotFoundError:
        print("The file was not found")
        return jsonify({"error": "The file was not found"}), 500
    except Exception as e:
        return jsonify({"error": f"Error uploading file: {str(e)}"}), 500

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