import abc
import json
import math
import datetime
import time
import os

SETTINGS_FILE_PATH = 'settings.json'
LOG_FILE_PATH = "auto_record.log"
REPORT_TEMPLATE_FILE_PATH = "report_template.json"

KEY_WIDTH = 'width'
KEY_HEIGHT = 'height'
KEY_FRAME_RATE = 'frameRate'
KEY_TIME_SCALE = 'timeScale'
KEY_LATITUDE = 'latitude'
KEY_LONGITUDE = 'longitude'
KEY_DAWN_BUFFER = 'dawnBufferMinutes'
KEY_DUSK_BUFFER = 'duskBufferMinutes'
KEY_IMAGE_TEMPLATE = 'imageTemplate'
KEY_LOG_FORMAT = "logFormat"
KEY_CREATE_VIDEO_COMMAND = "createVideoCommand"
KEY_UPLOAD_VIDEO_COMMAND = "uploadVideoCommand"
KEY_REPORT_FILE_PATH = "reportFile"
KEY_DEVICE = "device"

ECLIPTIC_INCLINATION = 28127./216000.*math.pi
ECLIPTIC_FACTOR = math.tan(ECLIPTIC_INCLINATION)

ISO_DATE_FORMAT = "%Y-%m-%d"
ISO_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"

REPORT_KEY_DATE = "date"
REPORT_KEY_START_TIME = "start"
REPORT_KEY_END_TIME = "end"
REPORT_KEY_EXACT_COORDINATES = "exactCoordinates"
REPORT_KEY_APPROXIMATE_COORDINATES = "approxCoordinates"
REPORT_KEY_TIME_SCALE = "timeScale"
REPORT_KEY_DEVICE = "device"
REPORT_KEY_PROXY_IMPLEMENTATION = "implementation"
REPORT_KEY_N_IMAGES = "nImages"


class TimeLapse:
    def __init__(self, camera_proxy):
        self.settings = None
        self.camera_proxy = camera_proxy
        self.running = False
        self.log = open(LOG_FILE_PATH, "w")

    def init_camera_proxy(self):
        self.log_message("Initializing camera proxy {}".format(self.camera_proxy.implementation_type))
        width = int(self.get_settings()[KEY_WIDTH])
        height = int(self.get_settings()[KEY_HEIGHT])
        self.log_message("Setting resolution to {}x{}".format(width, height))
        self.camera_proxy.init_camera((width, height))
        self.log_message("Camera initialized")

    def get_settings(self):
        if self.settings is None:
            with open(SETTINGS_FILE_PATH) as settings_file:
                self.settings = json.load(settings_file)
        return self.settings

    def take_picture(self, image_name):
        self.camera_proxy.take_picture(image_name)
        self.log_message("Created image {}".format(image_name))

    def auto_record_and_upload(self):
        self.log_message("Auto record and upload started.")
        self.auto_record()
        self.create_video()
        self.upload_video()
        self.log_message("Auto record and upload finished.")

    def auto_record(self):
        try:
            self.running = True
            self.init_camera_proxy()
            latitude = float(self.get_settings()[KEY_LATITUDE])
            longitude = float(self.get_settings()[KEY_LONGITUDE])
            dawn_buffer = float(self.get_settings()[KEY_DAWN_BUFFER])
            dusk_buffer = float(self.get_settings()[KEY_DUSK_BUFFER])
            current_time = datetime.datetime.now()
            day_limits = TimeLapse.get_day_limits(latitude, longitude)
            record_start_hour = day_limits[0] - dawn_buffer/60
            record_end_hour = day_limits[1] + dusk_buffer/60
            midnight_time = datetime.datetime(current_time.year, current_time.month, current_time.day, 0, 0, 0, 0)
            midnight = time.mktime(midnight_time.timetuple())
            record_start = midnight + 3600*record_start_hour
            record_end = midnight + 3600*record_end_hour
            self.log_message("Starting auto-daylight recording from {} to {}".format(record_start_hour, record_end_hour))

            frame_rate = float(self.get_settings()[KEY_FRAME_RATE])
            time_scale = float(self.get_settings()[KEY_TIME_SCALE])
            frame_period = time_scale * 1./frame_rate
            self.log_message("Recording every {} seconds for frame rate {} at 1:{} timescale".format(frame_period, frame_rate, time_scale))

            image_template = self.get_settings()[KEY_IMAGE_TEMPLATE]
            test_file = image_template % 0
            output_dir = os.path.dirname(test_file)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                self.log_message("Created output directory: {}".format(output_dir))

            init_time = time.time()
            if init_time < record_start or init_time > record_end:
                if init_time > record_end:
                    record_start += 86400
                    record_end += 86400
                delay = record_start - init_time
                self.log_message("Delaying start for {} seconds until dawn".format(delay))
                time.sleep(delay)

            self.log_message("Starting recording session")
            image_index = 1
            start_time = time.time()
            while self.running:
                image_name = image_template % image_index
                self.take_picture(image_name)
                if time.time() < record_end:
                    image_index += 1
                    time.sleep(frame_period - ((time.time() - start_time) % frame_period))
                else:
                    self.running = False
                    self.log_message("Ending recording session")
            self.create_report(latitude, longitude, record_start, record_end, time_scale, image_index)
        finally:
            self.camera_proxy.close_camera()

    def create_report(self, latitude, longitude, start_time, end_time, time_scale, n_images):
        report_file_path = self.get_settings()[KEY_REPORT_FILE_PATH]
        self.log_message("Creating report file {}".format(report_file_path))
        report_file = open(report_file_path, "w")
        with open(REPORT_TEMPLATE_FILE_PATH) as template_file:
            report_template = json.load(template_file)
        for i in xrange(len(report_template)):
            report_data_key = report_template[str(i+1)]
            if report_data_key == REPORT_KEY_DATE:
                print >>report_file, "Date: {}".format(time.strftime(ISO_DATE_FORMAT, time.gmtime(start_time)))
            elif report_data_key == REPORT_KEY_START_TIME:
                print >>report_file, "Start: {} UTC".format(time.strftime(ISO_TIME_FORMAT, time.gmtime(start_time)))
            elif report_data_key == REPORT_KEY_END_TIME:
                print >>report_file, "End: {} UTC".format(time.strftime(ISO_TIME_FORMAT, time.gmtime(end_time)))
            elif report_data_key == REPORT_KEY_EXACT_COORDINATES:
                print >>report_file, "Coordinates: {}N, {}E".format(latitude, longitude)
            elif report_data_key == REPORT_KEY_APPROXIMATE_COORDINATES:
                print >>report_file, "Approximate coordinates: {:.1f}N, {:.1f}E".format(latitude, longitude)
            elif report_data_key == REPORT_KEY_TIME_SCALE:
                print >>report_file, "Time scale: 1:{}".format(time_scale)
            elif report_data_key == REPORT_KEY_DEVICE:
                print >>report_file, "Recorded with: {}".format(self.get_settings()[KEY_DEVICE])
            elif report_data_key == REPORT_KEY_PROXY_IMPLEMENTATION:
                print >>report_file, "Recording implementation: {}".format(self.camera_proxy.implementation_type)
            elif report_data_key == REPORT_KEY_N_IMAGES:
                print >>report_file, "Number of images taken: {}".format(n_images)
        report_file.close()

    def create_video(self):
        create_video_command = self.get_settings()[KEY_CREATE_VIDEO_COMMAND]
        self.log_message("Creating video with command '{}'".format(create_video_command))
        os.system(create_video_command)

    def upload_video(self):
        upload_video_command = self.get_settings()[KEY_UPLOAD_VIDEO_COMMAND]
        self.log_message("Uploading video with command '{}'".format(upload_video_command))
        os.system(upload_video_command)

    def log_message(self, message):
        dated_message = (self.get_settings()[KEY_LOG_FORMAT]).format(time=datetime.datetime.now(), message=message)
        print dated_message
        print >>self.log, dated_message
        self.log.flush()

    @staticmethod
    def get_day_limits(latitude, longitude):
        current_date = datetime.datetime.now()
        spring_equinox = datetime.datetime(current_date.year, 3, 20)
        equinox_offset = (current_date - spring_equinox).days

        longitudinal_offset = longitude/15.
        timezone_offset = time.localtime().tm_hour - time.gmtime().tm_hour
        midday_offset = timezone_offset - longitudinal_offset

        if latitude < 90:
            acos_arg = -math.sin(equinox_offset/356.*2.*math.pi)*math.tan(math.radians(latitude))*ECLIPTIC_FACTOR
            if acos_arg > 1:
                return (12 + midday_offset, 12 + midday_offset)
            elif acos_arg < -1:
                return (0, 24)
            else:
                day_length = 24*math.acos(acos_arg)/math.pi
                day_start = 12 + midday_offset - day_length/2
                day_end = day_start + day_length
                return (day_start, day_end)
        else:
            if math.sin(equinox_offset/365.*2.*math.pi)*latitude > 0:
                return (12 + midday_offset, 12 + midday_offset)
            else:
                return (0, 24)


class AbstractCameraProxy:
    __metaclass__ = abc.ABCMeta

    def __init__(self, implementation_type):
        self.implementation_type = implementation_type

    @abc.abstractmethod
    def init_camera(self, resolution):
        pass

    @abc.abstractmethod
    def take_picture(self, image_name):
        pass

    @abc.abstractmethod
    def close_camera(self):
        pass
