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
from flask import jsonify


''' ADD ERROR HANDLING IN THIS CODE, to account for the case where the QR code generation fails, PDF upload failure ..
'''
def generate_qr_code(event_id, ticket_id, user_id, category_id):
    try:
        # Create QR Code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr_data = {
            "eventId": str(event_id),
            "ticketId": str(ticket_id),
            "userId": str(user_id),
            "ticketCategoryId": str(category_id)
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

def generate_ticket_pdf(qr_image_buffers, event_name, attendee_name, location, ticket_id, event_DateTime):
    # Create a BytesIO object to store the PDF data
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
        ['Date:', event_DateTime.strftime('%d %B, %Y')],
        ['Location:', location['Name']],
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

def upload_to_s3(file, bucket, file_name):
    print('Connecting to S3...')

    # Initialize a session using your credentials
    session = boto3.Session(
        aws_access_key_id= os.getenv('aws_access_key_id'),
        aws_secret_access_key= os.getenv('aws_secret_access_key'),
        region_name='eu-west-2'
    )
    # Initialize S3 client
    s3_client = session.client('s3')

    try:
        print('Uploading file...')
        response = s3_client.upload_fileobj(
            file,
            bucket,
            file_name
        )
        return jsonify({"message": "File uploaded successfully"}), 200
    except FileNotFoundError:
        print("The file was not found")
        return jsonify({"error": "The file was not found"}), 500
    except Exception as e:
        return jsonify({"error": f"Error uploading file: {str(e)}"}), 500
    
def delete_from_s3(bucket, file_name):
    session = boto3.Session(
        aws_access_key_id= os.getenv('aws_access_key_id'),
        aws_secret_access_key= os.getenv('aws_secret_access_key'),
        region_name='eu-west-2'
    )
    # Create an S3 client
    s3_client = session.client('s3')

    try:
        s3_client.delete_object(Bucket=bucket, Key=file_name)
        return jsonify({"message": "File deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": f"Error deleting file: {str(e)}"}), 500

def download_pdf_from_s3(key):
    session = boto3.Session(
        aws_access_key_id= os.getenv('aws_access_key_id'),
        aws_secret_access_key= os.getenv('aws_secret_access_key'),
        region_name='eu-west-2'
    )
    # Create an S3 client
    s3_client = session.client('s3')

    # Specify the bucket name and the key of the PDF to be deleted
    bucket = 'ticketpdfbucket'

    try:
        # Generate pre-signed URL
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket, 'Key': key},
            ExpiresIn=60
        )
        return url
    except Exception as e:
        return jsonify({"error": f"Error generating URL: {str(e)}"}), 500
