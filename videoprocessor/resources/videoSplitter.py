import cv2
import os
import base64
import config
import logging
from resources.producer import connect_kafka_producer, publish_message

# set logging level for 'video Processor'
log = logging.getLogger('root')


def videosplitter(key):
    try:
        # get SRS_CLUSTER URL from environment variable
        srs_cluster = os.getenv('SRS_CLUSTER')
        if srs_cluster is None:
            log.info("srs cluster not found in env")
            srs_cluster = config.Config.VIDEO_INPUT_PATH
        log.info("final srs cluster and key value is "+ srs_cluster + key)
        cap = cv2.VideoCapture(srs_cluster + key)
        cap.open(srs_cluster + key)
        isCapOpen = cap.isOpened()
        log.info('cap is opened : ' + str(isCapOpen))

        currentFrame = 0
        while cap.isOpened():
            # Capture frame-by-frame
            ret, frame = cap.read()

            # Convert frames into base64 encoded string
            ret, buffer = cv2.imencode('.jpg', frame)
            imageData = base64.b64encode(buffer)

            # Publishing frames to kafka topic
            kafka_producer = connect_kafka_producer()
            publish_message(kafka_producer, config.Config.KAFKA_TOPIC, 'frame', key, imageData)

            # Saves image of the current frame in jpg file
            name = '/frame' + str(currentFrame) + '.jpg'
            log.info('Creating...' + name)

            # To stop duplicate images
            currentFrame += 1

    except Exception as ex:
        log.error('Exception while splitting video')
        log.error(str(ex))

    finally:
        # When everything done, release the capture
        cap.release()
        cv2.destroyAllWindows()
