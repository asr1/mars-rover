import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import scipy
from scipy.interpolate import LSQUnivariateSpline

import sentinel
import sensors
import ir
import sonar
import servo


class Rover():
    """ TODO
    """

    def __init__(self, sen = None, calib_dir = None):
        """ TODO
        """
        if sen is None:
            sen = sentinel.Sentinel()
        elif type(sen) is str:
            sen = sentinel.Sentinel(str)
        elif type(sen) != sentinel.Sentinel:
            raise TypeError("The argument `sen` must be `None`, of type `str` "
                                                       "or of type `Sentinel`")
        self.sen = sen

        # Attempt to load the converters from `calib_dir`:
        if calib_dir == None:
            calib_dir = sensors.DEFAULT_CALIBRATION_DATA_DIR

        self.ir_conv = sensors.gen_ir_converter(calib_dir + "/ir.csv")
        self.sonar_conv = sensors.gen_sonar_converter(calib_dir + "/sonar.csv")
        self.servo_conv = sensors.gen_servo_converter(calib_dir + "/servo.csv")

        # Creates the empty list to store scan data generated from a position.
        # This is expected to be a list 2-tuples, where each element is an
        # `np.ndarray` object. The first element of a pair is the ir data 
        # generated by a scan, while the second element is sonar data generated
        # at that same time. For each of these arrays, their first column is
        # angles (in degrees) and the second column is the corresponding radial
        # distance (in cm) as measured in that reading and converted.
        self.scan_points = []

        self.scan_contours = []

        # Startup the figure and axis to be used for displaying scan data:
        self.scan_view = plt.figure().add_subplot(111, projection = 'polar')
        self.clear_scan()

        # Rover presents a map of those elements of the environment which it has
        # discovered. Scan and event data is mapped onto this cartesian space,
        # where the robot's initial location is at (0, 0) and it is initially
        # directed toward angle 0:
        self.x_loc = 0.0
        self.y_loc = 0.0
        self.direction = 0.0

        # Locations of various objects and events to be displayed on `env_view`:
        env = {
                # The dangers that the rover has found so far:
                "bumps": [],
                "cliffs": [],
                "drops": [],
                "tape": [],

                # Point observations found in scans and mapped to `env` space:
                "ir_obs": [],
                "sonar_obs": []

                # Object contours represented by regressions on the `obs` data:
                "contours": []
              }




    def scan(self, n, start = 0, end = 180):
        """ This communicates with the rover to generate distance data while
        making a single pass from angle `start` to angle `end`.

        The argument `n` indicates the number of distance readings to be
        recorded from both the IR sensor and the sonar sensor at each angle (up
        to and including the angle `end`).

        The results are returned as a pair of `np.ndarray` objects. The first
        is the IR data, while the second is the sonar data. Both of these
        arrays have two columns: the first column is the angle while the second
        column is the distance measurement.

        So, a method call will, in total, prompt

            2 * n * (abs(end - start) + 1)

        distance readings to be recorded and returned.

        Note that the scan can happen in either direction (i.e. clockwise or
        counter-clockwise) depending on which angle is bigger than the other.

        If and only if `update` is true, will the results of this scan be
        appended to the rover's `scan_points` list and the rover's `scan_view`
        will be updated.
        """

        if start <= end:
            angles = np.arange(start, end+1)
        else:
            angles = np.arange(start, end-1, -1)

        # The number of rows in each of the results arrays:
        num_rows = n * len(angles)

        ir_data = np.empty(shape = (num_rows, 2))
        sonar_data = np.empty(shape = (num_rows, 2))

        for (idx, angle) in enumerate(angles):

            servo.pulse(self.sen, self.servo_conv(angle))
            rows = [r for r in range(idx * n, (idx+1) * n)]

            ir_data[rows, 0] = angle
            ir_data[rows, 1] = ir.readings(self.sen, n)

            sonar_data[rows, 0] = angle
            sonar_data[rows, 1] = sonar.readings(self.sen, n)

        # Perform the conversion from raw readings to distances.
        ir_data[:, 1] = self.ir_conv(ir_data[:, 1])
        sonar_data[:, 1] = self.sonar_conv(sonar_data[:, 1])

        rv = (ir_data, sonar_data)
        append_scan(rv)
        return rv





    def append_scan(self, scan):
        """ Takes the given `scan` data and updates four things:

        (1) The `scan_points` list, by simply appending this data.
        (2) The `scan_view`, by adding this data to the radial scatter plot.
        (3) The `env["obs"]` by transforming this new `scan` data to the
            cartesian coordinate system displayed by `env_view`.
        (4) The `env_view` itself, by plotting the just added `scan_points`
        """

        # (1):
        self.scan_points.append(scan)

        # (2):
        ir_data, sonar_data = scan
        angles = ir_data[:, 0] * (np.pi / 180.0)
        self.scan_view.scatter(angles, ir_data[:, 1], 'g')
        angles = sonar_data[:, 0] * (np.pi / 180.0)
        self.scan_view.scatter(angles, sonar_data[:, 1], 'b')
        self.scan_view.figure.canvas.draw()

        # (3):
        ir_data = self.radial_to_env(ir_data[:, 0], ir_data[:, 1])
        sonar_data = self.radial_to_env(sonar_data[:, 0], sonar_data[:, 0])
        self.env["ir_obs"].append(ir_data)
        self.env["sonar_obs"].append(sonar_data)

        # (4):
        self.env_view.scatter(ir_data[:, 0], sonar_data[:, 1])
        self.env_view.figure.canvas.draw()




    def clear_scan(self):
        """ Clears the contents of `scan_points` and clears the `scan_view`. """
        self.scan_points = []
        self.scan_view.clear()
        self.scan_view.set_rmax(100)
        self.scan_view.figure.canvas.draw()  # Updates view




    def plot_obj_contours(self):
        """ Generates a regression for each independent object discovered in the
        current scan, and draws it onto both the `scan_view` and the `env_view`.
        """

        # TODO: Until a scan is finalized by moving, keep track of those
        # contours which were plotted so that they can be removed and updated
        # when new scan data arrives.

        raise NotImplementedError




    def radial_to_env(self, thetas, rs):
        """ Uses the rover's current orientation in the environment (i.e. its
        current location and angle) to map these radial points into the
        cartesian environment presented by `env_view`.

        `thetas` is an `np.ndarray` of angles (measured in degrees), and `rs` is
        a `np.ndarray` of the corresponding radial distances.

        A newly created `np.ndarray` with two columns returned. For each
        (theta, r) pair in the inputs, a single (x, y) coordinate will be in
        this returned array.
        """

        if len(thetas) != len(rs):
            raise ValueError("`thetas` and `rs` must be of the same length.")

        # Make the given angles w.r.t. the 0 degrees of the `env`, convert
        # them to radians, and make a copy them to the other column:
        rv = np.empty((len(rs), 2), dtype = np.float64)
        rv[:, 0] = thetas - 90.0 + self.direction
        rv[:, 0] *= np.pi / 180.0
        rv[:, 1] = rv[:, 0]

        # Find the `x` and `y` values w.r.t. the origin of `env`:
        rv[:, 0] = rs * np.cos(rv[:, 0]) + self.x_loc
        rv[:, 1] = rs * np.sin(rv[:, 1]) + self.y_loc

        return rv




    def danger_found(self, danger_id):
        """ Appends a new danger to the appropriate list of `env`, and updates
        the `env_view`. The position at which the danger is placed is computed
        based on the rover's location and direction, but also where on the robot
        that particular danger-detection sensor is located. """
        
        raise NotImplementedError




    def _obj_contours(self):
        """ Looks at the current contents of `scan_points` and uses it to
        generate a list of regressions that define the contours of observed
        objects. Each element in the list is considered to be a distinct object.
        """

        # TODO: ignore objects that have very small angular width.

        raise NotImplementedError

        knots = np.linspace(0, 180, 61)
        return LSQUnivariateSpline(data[:, 0], data[:, 1])
