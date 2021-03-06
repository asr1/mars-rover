# servo.py

import struct

from codes import MesgID, SubsysID, ServoCommand


def init(sen):
    """
    Initializes the servo subsystem for use. Also activates the servo, i.e.,
    the servo state is made to be "on".
    """

    sen.tx_mesg(MesgID.command, SubsysID.servo, ServoCommand.init, None)
    sen.rx_mesg(MesgID.command, SubsysID.servo, ServoCommand.init, False)




def calibrate(sen):
    """
    Initiates the `control`-operated calibration routine of the servo subsystem.
    """

    raise NotImplementedError()
    # TODO



def state(sen, s = None):
    """
    Gets and sets the servo's state. If the function is invoked with no
    arguments, or if it is passed `None`, then it returns the servos current
    state as a string, either "on" or "off". If the function is passed "on",
    then the servo will be turned on, and if it is passed "off", then the
    servo will be turned off.
    """

    if s == None:
        sen.tx_mesg(MesgID.command, SubsysID.servo, ServoCommand.state, False)
        rv = sen.rx_mesg(MesgID.command, SubsysID.servo, ServoCommand.state, True)
        rv = "on" if rv == b'\x01' else "off"
    elif s == "on":
        init(sen)
        rv = "on"
    elif s == "off":
        # TODO: How would I tell the servo to turn off?? Send a 0? Make 
        # consistent on rover side
        b = struct.pack("<I", 0)
        sen.tx_mesg(MesgID.command, SubsysID.servo, ServoCommand.state, b)
        sen.rx_mesg(MesgID.command, SubsysID.servo, ServoCommand.state, False)
        rv = "off"
    else:
        raise ValueError('Argument `s` must be `None`, "on", or "off".');

    return rv





def angle(sen, angle, wait = True):
    """
    Expects `angle` to be an integer in the range [0..180]. The servo will be
    moved to this angle. If `wait` is `True`, then the following will happen:

    (1) The `rover` will stream status signals indicating "not-finished" until
    it believes that the servo has actually reached the indicated angle, then
    it sends "finished" signal.

    (2) At the same time, the function will continue to block until it receives
    this "finished" signal.
    """
    
    if not (0 <= angle and angle  <= 180):
        raise ValueError("Argument `angle` must be an integer in [0..180].")
    
    b = struct.pack("<I", angle)
    tx_mesg(MesgID.command, SubsysID.servo, ServoCommand.angle, b)
    b = sen.rx_mesg(MesgID.command, SubsysID.servo, ServoCommand.angle, True)
    # TODO: Check that the response data in `b` is well-formed.




def pulse_width(sen, pw):
    """
    Sets `pw` to be the new pulse width for the servo's PWM cycle, i.e. the
    number of clock-ticks for which the cycle is logical-high.

    Expects an appropriately sized integer number. The range of appropriate
    values is dependent upon the servo's calibration.

    Sends a single 16-bit integer in the data segment of the sending message.
    Expects nothing in the response message's data segment
    """

    if not (0.0 < p and p < 1.0):
        raise ValueError("Argument `p` must be a float in the interval (0, 1).")

    b = struct.pack("<H", pw)
    sen.tx_mesg(MesgID.command, SubsysID.servo, ServoCommand.pulse_width, b)
    sen.rx_mesg(MesgID.command, SubsysID.servo, ServoCommand.pulse_width, False)
