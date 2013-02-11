#!/usr/bin/env python
import cv
import motion
import os
import Image
import logging
import freenect
import numpy as np
from datetime import datetime
from time import sleep

import smtplib
from email import Encoders
from email.MIMEBase import MIMEBase
from email.MIMEMultipart import MIMEMultipart
from email.Utils import formatdate

HOST = "smtp.gmail.com:587"
EMAIL_FROM = 'spawnedc@gmail.com'
EMAIL_TO = ['spawnedc@gmail.com']
EMAIL_SUBJECT = 'Evde biseyler oluyo!'
USERNAME = 'spawnedc@gmail.com'
PASSWORD = ''
COMMASPACE = ', '

# Kinect constants:

# DEPTH_10BIT
# DEPTH_10BIT_PACKED
# DEPTH_11BIT
# DEPTH_11BIT_PACKED
# DEVICE_AUDIO
# DEVICE_CAMERA
# DEVICE_MOTOR
# LED_BLINK_GREEN
# LED_BLINK_RED_YELLOW
# LED_GREEN
# LED_OFF
# LED_RED
# LED_YELLOW
# RESOLUTION_HIGH
# RESOLUTION_LOW
# RESOLUTION_MEDIUM
# VIDEO_BAYER
# VIDEO_IR_10BIT
# VIDEO_IR_10BIT_PACKED
# VIDEO_IR_8BIT
# VIDEO_RGB
# VIDEO_YUV_RAW
# VIDEO_YUV_RGB

class Vahey:

    capture_folder = 'captures'
    filename_format = '%s.png'
    datetime_format = '%d-%m-%y-%H-%M-%S'
    sensitivity = 0.08

    kinect = None

    def __init__(self, cam=-1):
        # Initialize freenect and get the context
        context = freenect.init()
        # Open the device and get the device
        self.kinect = freenect.open_device(context, 0)
        # Turn the led off
        freenect.set_led(self.kinect, freenect.LED_OFF)
        # Close the device
        freenect.close_device(self.kinect)

    def capture_image(self, filename=None):
        if not filename:
            filename = datetime.now().strftime(self.datetime_format)

        filename = os.path.join(self.capture_folder, self.filename_format % filename)

        rgb, _ = freenect.sync_get_video()
        na = np.array(rgb[::1,::-1,::-1])
        frame = cv.fromarray(na)

        cv.SaveImage(filename, frame)
        return (filename, frame)

    def get_diff(self, delay=0.5):
        filename1, frame1 = self.capture_image('1')
        sleep(delay)
        filename2, frame2 = self.capture_image('2')

        self.image1 = Image.open(filename1)
        self.image2 = Image.open(filename2)

        self.diff = motion.images_diff(self.image1, self.image2)
        return self.diff

    def send_email(self, im):

        msg = MIMEMultipart()
        msg["From"] = EMAIL_FROM
        msg["To"] = COMMASPACE.join(EMAIL_TO)
        msg["Subject"] = EMAIL_SUBJECT
        msg['Date']    = formatdate(localtime=True)

        part = MIMEBase('application', "octet-stream")
        part.set_payload( open(im.filename, "rb").read() )
        Encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(im.filename))
        msg.attach(part)

        server = smtplib.SMTP(HOST)
        server.starttls()
        server.login(USERNAME, PASSWORD)

        try:
            server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
            server.close()
        except Exception, e:
            error_msg = "Unable to send email. Error: %s" % str(e)
            print error_msg

    def start(self):
        while True:
            diff = self.get_diff()

            if diff > self.sensitivity:
                logging.warning('Motion detected! (%s)' % diff)

                self.send_email(self.image2)

                filename, frame = self.capture_image()

            else:
                logging.warning('Nothing yet. (%s)' % diff)


if __name__ == '__main__':
    vah = Vahey()
    vah.start()