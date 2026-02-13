import sys
import time
import json
import logging
from pathlib import Path

import cv2
import numpy as np
import paho.mqtt.client as mqtt

try:
    import mediapipe as mp
except ImportError:
    mp = None

from . import config
from .haar_5pt import Haar5ptDetector, align_face_5pt
from .embed import ArcFaceEmbedderONNX


# -------------------------------
# Setup logging
# -------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# -------------------------------
# MQTT Configuration
# -------------------------------
MQTT_BROKER = getattr(config, 'MQTT_BROKER', '157.173.101.159')
MQTT_PORT = getattr(config, 'MQTT_PORT', 1883)
MQTT_CLIENT_ID = getattr(config, 'MQTT_CLIENT_ID', 'pc_vision_node')
TEAM_ID = getattr(config, 'TEAM_ID', 'mchiir01')
MQTT_TOPIC = f"vision/{TEAM_ID}/movement"


# -------------------------------
# Database & Utility Functions
# -------------------------------
def load_database():
    """Load enrolled face database from NPZ file."""
    if not config.DB_NPZ_PATH.exists():
        return {}
    data = np.load(str(config.DB_NPZ_PATH), allow_pickle=True)
    return {k: data[k].astype(np.float32) for k in data.files}


def cosine_distance(a, b):
    """Compute cosine distance between two vectors."""
    a = a.reshape(-1).astype(np.float32)
    b = b.reshape(-1).astype(np.float32)
    return 1.0 - float(np.dot(a, b))


def detect_face_movement(prev_center_x, center_x):
    """
    Detect face movement direction.
    Returns: "MOVE_LEFT", "MOVE_RIGHT", or "CENTERED"
    """
    if prev_center_x is None:
        return "CENTERED"
    
    dx = center_x - prev_center_x
    
    if dx <= -config.LOCK_MOVEMENT_THRESHOLD_PX:
        return "MOVE_LEFT"
    elif dx >= config.LOCK_MOVEMENT_THRESHOLD_PX:
        return "MOVE_RIGHT"
    else:
        return "CENTERED"


# -------------------------------
# MQTT Publisher Class
# -------------------------------
class MQTTPublisher:
    """MQTT publisher for face lock movements."""
    
    def __init__(self, broker=MQTT_BROKER, port=MQTT_PORT, client_id=MQTT_CLIENT_ID):
        self.broker = broker
        self.port = port
        self.client_id = client_id
        self.topic = MQTT_TOPIC
        self.client = None
        self.connected = False
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback for MQTT connection."""
        if rc == 0:
            self.connected = True
            logger.info(f"Connected to MQTT broker at {self.broker}:{self.port}")
        else:
            logger.error(f"Failed to connect to MQTT broker. Error code: {rc}")
    
    def on_disconnect(self, client, userdata, rc):
        """Callback for MQTT disconnection."""
        self.connected = False
        if rc != 0:
            logger.warning(f"Unexpected disconnection. Error code: {rc}")
    
    def on_publish(self, client, userdata, mid):
        """Callback for message publish."""
        pass
    
    def connect(self):
        """Connect to MQTT broker."""
        try:
            self.client = mqtt.Client(client_id=self.client_id)
            self.client.on_connect = self.on_connect
            self.client.on_disconnect = self.on_disconnect
            self.client.on_publish = self.on_publish
            
            self.client.connect(self.broker, self.port, keepalive=60)
            self.client.loop_start()
            
            # Wait for connection
            max_retries = 10
            for _ in range(max_retries):
                if self.connected:
                    return True
                time.sleep(0.5)
            
            logger.warning(f"Connection timeout after {max_retries * 0.5} seconds")
            return False
        except Exception as e:
            logger.error(f"Error connecting to MQTT broker: {e}")
            return False
    
    def publish_movement(self, status, confidence, timestamp=None):
        """Publish face movement to MQTT."""
        if timestamp is None:
            timestamp = int(time.time())
        
        payload = {
            "status": status,
            "confidence": round(confidence, 4),
            "timestamp": timestamp
        }
        
        try:
            result = self.client.publish(self.topic, json.dumps(payload), qos=1)
            if result.rc != mqtt.MQTT_ERR_SUCCESS:
                logger.error(f"Failed to publish message. Error code: {result.rc}")
        except Exception as e:
            logger.error(f"Error publishing movement: {e}")
    
    def disconnect(self):
        """Disconnect from MQTT broker."""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False
            logger.info("Disconnected from MQTT broker")


# -------------------------------
# Main Vision Node
# -------------------------------
def main():
    """Vision node: detect locked face movements and publish to MQTT."""
    db = load_database()
    if not db:
        logger.error("No enrolled identities. Run: python -m src.enroll")
        return False
    
    names = sorted(db.keys())
    logger.info(f"Enrolled identities: {names}")
    
    # Lock onto first identity
    lock_identity = names[0]
    logger.info(f"Will lock onto: {lock_identity}")
    
    config.ensure_dirs()
    
    # Initialize MQTT publisher
    mqtt_publisher = MQTTPublisher()
    if not mqtt_publisher.connect():
        logger.warning("Could not connect to MQTT broker, continuing...")
    
    # Initialize detectors
    detector = Haar5ptDetector(min_size=config.HAAR_MIN_SIZE, smooth_alpha=0.8, debug=False)
    embedder = ArcFaceEmbedderONNX(config.ARCFACE_MODEL_PATH)
    
    embeddings_matrix = np.stack([db[n].reshape(-1) for n in names], axis=0)
    lock_idx = names.index(lock_identity)
    threshold = config.DEFAULT_DISTANCE_THRESHOLD
    
    # Open camera
    cap = cv2.VideoCapture(config.CAMERA_INDEX)
    if not cap.isOpened():
        logger.error("Cannot open camera.")
        mqtt_publisher.disconnect()
        return False
    
    # State variables
    locked = False
    fail_count = 0
    prev_center_x = None
    frame_idx = 0
    last_publish_time = time.time()
    publish_interval = 0.1  # Publish at most every 100ms
    
    logger.info("Vision node started. Press 'q' to quit.")
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_idx += 1
            H, W = frame.shape[:2]
            faces = detector.detect(frame, max_faces=5)
            
            current_status = "NO_FACE"
            confidence = 0.0
            
            if not locked:
                # Looking for lock
                for face in faces:
                    aligned, _ = align_face_5pt(frame, face.kps, out_size=(112, 112))
                    res = embedder.embed(aligned)
                    query_emb = res.embedding
                    
                    dists = np.array([cosine_distance(query_emb, embeddings_matrix[i]) 
                                     for i in range(len(names))])
                    best_idx = int(np.argmin(dists))
                    best_dist = dists[best_idx]
                    
                    if best_idx == lock_idx and best_dist <= threshold:
                        locked = True
                        fail_count = 0
                        prev_center_x = (face.x1 + face.x2) / 2.0
                        logger.info(f"LOCKED onto {lock_identity}")
                        confidence = 1.0 - best_dist
                        current_status = "CENTERED"
                        break
            else:
                # Tracking locked face
                matched_face = None
                best_dist = 1.0
                
                for face in faces:
                    aligned, _ = align_face_5pt(frame, face.kps, out_size=(112, 112))
                    res = embedder.embed(aligned)
                    query_emb = res.embedding
                    
                    dists = np.array([cosine_distance(query_emb, embeddings_matrix[i]) 
                                     for i in range(len(names))])
                    idx = int(np.argmin(dists))
                    d = dists[idx]
                    
                    if idx == lock_idx and d <= threshold:
                        matched_face = face
                        best_dist = d
                        fail_count = 0
                        break
                    if len(faces) == 1 and d < 0.5:
                        matched_face = face
                        best_dist = d
                        fail_count += 1
                        if fail_count > 5:
                            matched_face = None
                        break
                
                if matched_face is None:
                    fail_count += 1
                    if fail_count >= config.LOCK_RELEASE_FRAMES:
                        locked = False
                        prev_center_x = None
                        logger.info("Lock released (face not seen)")
                        current_status = "NO_FACE"
                        confidence = 0.0
                else:
                    # Face is matched and locked
                    center_x = (matched_face.x1 + matched_face.x2) / 2.0
                    current_status = detect_face_movement(prev_center_x, center_x)
                    confidence = 1.0 - best_dist
                    prev_center_x = center_x
            
            # Publish movement with throttling
            current_time = time.time()
            if locked and (current_time - last_publish_time) >= publish_interval:
                mqtt_publisher.publish_movement(
                    status=current_status,
                    confidence=confidence,
                    timestamp=int(current_time * 1000)  # Milliseconds
                )
                last_publish_time = current_time
            
            # -------------------------------
            # Display camera feed
            # -------------------------------
            display_text = f"{lock_identity if locked else 'Searching'} | {current_status} | {confidence:.2f}"
            cv2.putText(frame, display_text, (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            
            # Draw face bounding boxes
            for face in faces:
                cv2.rectangle(frame, (face.x1, face.y1), (face.x2, face.y2), (255, 0, 0), 2)
            
            cv2.imshow("Face Lock Vision", frame)
            
            # Exit on 'q' key
            if cv2.waitKey(1) & 0xFF == ord('q'):
                logger.info("User requested exit.")
                break
    
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Error in vision loop: {e}", exc_info=True)
    finally:
        cap.release()
        cv2.destroyAllWindows()
        mqtt_publisher.disconnect()
        logger.info("Vision node stopped.")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)