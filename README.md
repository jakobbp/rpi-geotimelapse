# rpi-geotimelapse
Geographically enhanced time-lapse application aimed towards Raspberry Pi and its camera modules.

## About
GeoTimeLapse captures still images from raspberry pi camera module during daytime.
Daytime hours are determined by the provided geographic coordinates.

## Usage
Running the following will start a recording session on a Raspberry Pi using `picamera` module:
```bash
python rpiusage.py
```

Running the following will start a recording session using video device 0 and `cv2` module:
```bash
python genericusage.py
```

Session parameters (such as resolution, time scale, targetted video framerate, etc.) will be read from settings file `settings.json`.
For details about `settings.json` see [Settings](#settings) section.

Session's appropriate start and end time will be calculated from the *latitude* and *longitude* provided in settings file.
Once the recording is finished, a report text file will be generated using the report template `report_template.json`.
This is separate from the process log, which is written both to *stdout* and to `auto_record.log`.
Afterwards, the generated sequence of images will be combined into a video and uploaded,
if corresponding commands are provided in settings.

## Settings
Settings should very seldom change between recording sessions. In order to avoid passing numerous immutable parameters at every launch,
they are stored in a human-readable *JSON* format inside `settings.json` file.

Settings are:
 - **`width`**: recorded image width,
 - **`height`**: recorded image height,
 - **`frameRate`**: targetted frame rate of the final video,
 - **`timeScale`**: time scale of the final video at the targetted frame rate,
 - **`latitude`**: latitude - N-S coordinate in geographic coordinate system,
 - **`longitude`**: longitude - E-W coordinate in geographic coordinate system,
 - **`dawnBufferMinutes`**: number of minutes that recording should start before dawn,
 - **`duskBufferMinutes`**: number of minutes that recording should stop after dusk,
 - **`imageTemplate`**: image filename template,
 - **`logFormat`**: log formatting (recognizes parameters `time` and `message`),
 - **`createVideoCommand`**: system command to run to create video from images,
 - **`uploadVideoCommand`**: system command to run to upload the created video,
 - **`reportFile`**: session report file path and
 - **`device`**: name of the device the photos will be taken with (can be included into the session's report).

### Frame Rate, Time Scale and Image Frequency
The frequency of taking images is determined by both frame rate and time scale.
While **frame rate** of the final video is quite unambiguously defined term, **time scale** is very much less so.

Time scale is the ratio between the number of time unit in the final video
and a single same time unit in real time.
For instance, if the desired effect is for 10 seconds in the final video to represent 1 hour of real time,
then the time scale is:
```text
timeScale = 1h/10s = 3600s/10s = 360
```

From these two parameters the application derives, the period between taking frames, or **image frequency**.
Delay between taking images is thus derived as:
```text
delay = timeScale/frameRate
```
which leads to an image being taken every 6 seconds for a given time scale 360 and targetted frame rate of 60 FPS.

### Report Settings
Session's report is conveniently aggregated data about the location, time and device used for the recording.
Report is written into a file immediately after the the image taking loop stops,
where the path to the report file is specified in settings file.

Report is generated according to report template `report_template.json`.
Template defines the included report data fields and their ordering by including them in the template file
and enumerating them (`"[field_order]": "[data_field]"`).

Recognized data fields are:
 - **`date`**: start date of the recording in ISO format,
 - **`start`**: start time of the recording in ISO format,
 - **`end`**: end time of the recording in ISO format,
 - **`exactCoordinates`**: exact geographic coordinates of the place of the recording,
 - **`approxCoordinates`**: geographic coordinates of the place of the recording rounded to first decimal (for privacy),
 - **`timeScale`**: targetted time scale for the recording (corresponds to `timeScale` in settings file),
 - **`device`**: name of the device the photos were be taken with (corresponds to `device` in settings file),
 - **`implementation`**: description of the camera proxy class implementation used for taking the pictures and
 - **`nImages`**: total number of images taken during the recording.

## Extensions
Capturing images is not limited to `picamera` and `cv2` modules.
`TimeLapse` class interacts with capture devices via small abstract wrapper class `AbstractCameraProxy`,
which can be extended to provide image capturing capabilities using different ways.
This abstract class declares the following three abstract methods:
 - **`init_camera(self, resolution)`**: initializes the video device and sets image resolution,
 - **`take_picture(self, image_name)`**: captures and saves a picture with the given filename and
 - **`close_camera(self)`**: closes the vide device.

To use `TimeLapse` with a custom camera proxy, first create a class using AbstractCameraProxy as base,
then override the above methods as appropriate and
finally pass an instance of this camera proxy implementation to `TimeLapse` as the constructor parameter.

A short and simple example of this is the [implementation of picamera proxy](rpiusage.py).
