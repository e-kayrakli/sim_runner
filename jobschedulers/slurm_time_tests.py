#!/usr/bin/env python3

import unittest

class SlurmTime(object):
    _time = 0

    def __init__(self, time=0):
        if isinstance(time, str):
            self._time = self.conv_slurm_time_to_sec(time)
        if isinstance(time, int):
            self._time = time

    def __str__(self):
        return SlurmTime.format_slurm_time(self._time)

    def getSeconds(self):
        return self._time

    @staticmethod
    def format_slurm_time(time):
        seconds = int(time % 60)
        minutes = int((time / 60) % 60)
        hours = int((time / 60 / 60) % 24)
        days = int(time / 60 / 60 / 24)

        if days != 0:
            return '%(days)d-%(hours)02d:%(minutes)02d:%(seconds)02d' % locals()
        if hours != 0:
            return '%(hours)02d:%(minutes)02d:%(seconds)02d' % locals()

        return '%(minutes)d:%(seconds)02d' % locals()

    @staticmethod
    def conv_slurm_time_to_sec(s):
        """Convert a slurm time format string (04-01:04:00) to its equivalent
        in seconds."""
        days = 0
        if s.find('-') != -1:
            (days, time) = s.split('-')
            days = int(days) * 24 * 3600
            s = time
        return int(days) + SlurmTime.conv_hours_to_sec(s)

    @staticmethod
    def conv_hours_to_sec(s):
        """Convert a string formated as 01:00:00 to its equivalent in seconds"""
        if s.count(':') == 2:
            (hours, minutes, seconds) = s.split(':')
        else:
            (minutes, seconds) = s.split(':')
            hours = 0
        return (int(hours) * 3600 +
                int(minutes) * 60 +
                int(seconds))

class SlurmTimeTest(unittest.TestCase):
    def testCreation(self):
        st = SlurmTime('01-20:01:02')
        self.assertTrue(st._time == 158462)
        self.assertTrue(str(st) == '1-20:01:02')
        st = SlurmTime('18:00:00')
        self.assertTrue(str(st) == '18:00:00')
        st = SlurmTime('3:00')
        self.assertTrue(str(st) == '3:00')

def main():
    unittest.main()

if __name__ == '__main__':
    main()

