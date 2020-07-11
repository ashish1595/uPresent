import numpy as np
import imutils
import pickle
import cv2
import os
import constants
import logging

log = logging.getLogger("root")


def recog(image):
    embedding_model = constants.MODEL_FILES_DIR + "/openface_nn4.small2.v1.t7"
    log.info("embedding_model..." + embedding_model)
    conf = 0.5
    recognizer = constants.PICKLE_FILES_DIR + "/recognizer.pickle"
    l = constants.PICKLE_FILES_DIR + "/le.pickle"
    log.info("[INFO] loading face detector...")
    try:
        proto_path = constants.MODEL_FILES_DIR + "/deploy.prototxt"
        model_path = (
            constants.MODEL_FILES_DIR + "/res10_300x300_ssd_iter_140000.caffemodel"
        )
        detector = cv2.dnn.readNetFromCaffe(proto_path, model_path)
        # load our serialized face embedding model from disk
        log.info("[INFO] loading face recognizer...")
        embedder = cv2.dnn.readNetFromTorch(embedding_model)
        # load the actual face recognition model along with the label encoder
        recognizer = pickle.loads(open(recognizer, "rb").read())
        le = pickle.loads(open(l, "rb").read())

        # load the image, resize it to have a width of 600 pixels (while
        # maintaining the aspect ratio), and then grab the image dimensions
        image = cv2.imread(image)
        image = imutils.resize(image, width=600)
        (h, w) = image.shape[:2]

        # construct a blob from the image
        image_blob = cv2.dnn.blobFromImage(
            cv2.resize(image, (300, 300)),
            1.0,
            (300, 300),
            (104.0, 177.0, 123.0),
            swapRB=False,
            crop=False,
        )

        # apply OpenCV's deep learning-based face detector to localize
        # faces in the input image
        detector.setInput(image_blob)
        detections = detector.forward()

        # loop over the detections
        for i in range(0, detections.shape[2]):
            # extract_embeddings the confidence (i.e., probability) associated with the
            # prediction
            confidence = detections[0, 0, i, 2]

            # filter out weak detections
            if confidence > conf:
                # compute the (x, y)-coordinates of the bounding box for the
                # face
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                (startX, startY, endX, endY) = box.astype("int")

                # extract_embeddings the face ROI
                face = image[startY:endY, startX:endX]
                (fH, fW) = face.shape[:2]

                # ensure the face width and height are sufficiently large
                if (
                    fW < constants.MIN_DETECTED_FACE_WIDTH
                    or fH < constants.MIN_DETECTED_FACE_HEIGHT
                ):
                    continue

                # construct a blob for the face ROI, then pass the blob
                # through our face embedding model to obtain the 128-d
                # quantification of the face
                face_blob = cv2.dnn.blobFromImage(
                    face, 1.0 / 255, (96, 96), (0, 0, 0), swapRB=True, crop=False
                )
                embedder.setInput(face_blob)
                vec = embedder.forward()

                # perform classification to recognize the face
                preds = recognizer.predict_proba(vec)[0]
                j = np.argmax(preds)
                probability = preds[j]
                name = le.classes_[j]

        # show the output image
        return name, probability * 100
    except Exception as ex:
        log.error(
            "Exception occurred while trying to recognize image. Exception msg: "
            + str(ex)
        )
        return {"Exception occurred. Exception msg: ": str(ex)}, 500
