from flask import Flask, request, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import os
import logging

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('media_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///media_history.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class MediaEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(500))
    title = db.Column(db.String(200))
    duration = db.Column(db.Float)
    total_duration = db.Column(db.Float)
    format = db.Column(db.String(50))
    video_format = db.Column(db.String(50))
    audio_codec = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    hostname = db.Column(db.String(100))
    ip_address = db.Column(db.String(50))
    status = db.Column(db.String(50), default='playing')

    def to_dict(self):
        return {
            'filename': self.filename,
            'title': self.title,
            'duration': self.duration,
            'total_duration': self.total_duration,
            'format': self.format,
            'video_format': self.video_format,
            'audio_codec': self.audio_codec,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'hostname': self.hostname,
            'ip_address': self.ip_address,
            'status': self.status
        }

@app.route('/')
def index():
    logger.debug("Accessing index page")
    entries = MediaEntry.query.order_by(MediaEntry.timestamp.desc()).all()
    for entry in entries:
        if entry.total_duration is None:
            entry.total_duration = 1
    logger.debug(f"Found {len(entries)} entries")
    return render_template('index.html', entries=entries)

@app.route('/track', methods=['POST'])
def track():
    try:
        data = request.get_json()
        logger.debug(f"Received track request data: {data}")

        entry = MediaEntry(
            filename=data.get('filename'),
            title=data.get('title'),
            duration=float(data.get('duration', 0)),
            total_duration=float(data.get('total_duration', 0)),
            format=data.get('format'),
            video_format=data.get('video_format'),
            audio_codec=data.get('audio_codec'),
            timestamp=datetime.fromtimestamp(data.get('timestamp')),
            hostname=data.get('hostname'),
            ip_address=request.remote_addr,
            status='playing'
        )

        db.session.add(entry)
        db.session.commit()
        logger.info(f"Successfully saved media entry to database with id {entry.id}")
        return {'status': 'success', 'id': entry.id}

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        return {'status': 'error', 'message': str(e)}, 500

@app.route('/update', methods=['POST'])
def update():
    logger.debug("Received update POST request")

    try:
        data = request.get_json()
        logger.debug(f"Received update data: {json.dumps(data, indent=2)}")

        entry = MediaEntry.query.filter_by(id=data.get('id')).first()
        if entry:
            entry.duration = data.get('duration')
            entry.status = data.get('status')  # Update status (terminated or playing)
            db.session.commit()
            logger.info(f"Updated media entry with ID {data.get('id')}")
            return {'status': 'success'}
        else:
            return {'status': 'error', 'message': 'Media entry not found'}, 404

    except Exception as e:
        logger.error(f"Error processing update request: {str(e)}", exc_info=True)
        return {'status': 'error', 'message': str(e)}, 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        logger.info("Database initialized")

    logger.info("Starting Flask server")
    app.run(debug=True)
