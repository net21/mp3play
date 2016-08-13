import random

from ctypes import windll, create_unicode_buffer

class _mci:
    def __init__(self):
        self.w32mci = windll.winmm.mciSendStringW
        self.w32mcierror = windll.winmm.mciGetErrorStringW

    def send(self, command):
        buffer = create_unicode_buffer(255)
        errorcode = self.w32mci(command, buffer, 254, 0)
        if errorcode:
            return errorcode, self.get_error(errorcode)
        else:
            return errorcode, buffer.value

    def get_error(self, error):
        error = int(error)
        buffer = create_unicode_buffer(255)
        self.w32mcierror(error, buffer, 254)
        return buffer.value

    def directsend(self, txt):
        (err, buf) = self.send(txt)
        if err != 0:
            print u'Error %s for "%s": %s' % (err, txt, (buf))
        return (err, buf)

# TODO: detect errors in all mci calls
class AudioClip(object):
    def __init__(self, filename):
        filename = filename.replace('/', '\\')
        self.filename = filename
        self._alias = 'mp3_%s' % str(random.random())

        self._mci = _mci()

        self._mci.directsend(u'open "%s" alias %s' % (filename, self._alias ))
        self._mci.directsend(u'set %s time format milliseconds' % self._alias)

        err, buf=self._mci.directsend(u'status %s length' % self._alias)
        self._length_ms = int(buf)
        print self._length_ms

    def volume(self, level):
        """Sets the volume between 0 and 100."""
        self._mci.directsend(u'setaudio %s volume to %d' %
                (self._alias, level * 10) )

    def play(self, start_ms=None, end_ms=None):
        start_ms = 0 if not start_ms else start_ms
        end_ms = self.milliseconds() if not end_ms else end_ms
        err,buf=self._mci.directsend(u'play %s from %d to %d'
                % (self._alias, start_ms, end_ms) )

    def isplaying(self):
        return self._mode() == 'playing'

    def _mode(self):
        err, buf = self._mci.directsend(u'status %s mode' % self._alias)
        return buf

    def pause(self):
        self._mci.directsend(u'pause %s' % self._alias)

    def unpause(self):
        self._mci.directsend(u'resume %s' % self._alias)

    def ispaused(self):
        return self._mode() == 'paused'

    def stop(self):
        self._mci.directsend(u'stop %s' % self._alias)
        self._mci.directsend(u'seek %s to start' % self._alias)

    def milliseconds(self):
        return self._length_ms

    # TODO: this closes the file even if we're still playing.
    # no good.  detect isplaying(), and don't die till then!
    def __del__(self):
        self._mci.directsend(u'close %s' % self._alias)
