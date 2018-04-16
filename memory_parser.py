import time
import re

from logster.logster_helper import MetricObject, LogsterParser
from logster.logster_helper import LogsterParsingException

class MemoryParser(LogsterParser):
    MEMORY_MEASURES = [
        'memory_total',
        'memory_rss',
        'memory_cache',
        'memory_swap',
        'memory_quota',
    ]

    def __init__(self, option_string=None):
        self.web_dyno_regex = re.compile('source=web\.')
        self.memory_measure_regexes = dict(
            (
                memory_measure,
                re.compile('.*\\bsample#%(memory_measure)s=(?P<%(memory_measure)s>[\\d.]+)MB\\b' % {'memory_measure': memory_measure}),
            ) for memory_measure in MemoryParser.MEMORY_MEASURES
        )

    def parse_line(self, line):
        try:
            is_web_dyno = self.web_dyno_regex.match(line)
            if is_web_dyno:
                for memory_measure in MemoryParser.MEMORY_MEASURES:
                    regex = self.memory_measure_regexes[memory_measure]
                    memory_measure_match = regex.match(line)
                    if memory_measure_match:
                        setattr(self, memory_measure, float(memory_measure_match.groupdict()[memory_measure]))
                    else:
                        raise LogsterParsingException('Failed to find one or more memory measures')
            else:
                raise LogsterParsingException('Not a web dyno')
        except Exception as e:
            raise LogsterParsingException('regmatch or contents failed with %s' % e)

    def get_state(self, _duration):
        return list(map(
            lambda memory_measure: MetricObject(
                'prod.system.%(memory_measure)s' % {'memory_measure': memory_measure},
                getattr(self, memory_measure) if hasattr(self, memory_measure) else None,
                '%(memory_measure)s in MB' % {'memory_measure': memory_measure},
            ),
            MemoryParser.MEMORY_MEASURES
        ))
