"""Synthetic sampling utilities for telemetry demos.

This module provides small utilities to generate synthetic telemetry samples
for link bandwidth utilization and latency. It is intentionally lightweight and
deterministic in shape but randomized in parameters so it can be used to
exercise dashboards, monitoring pipelines or unit tests that expect
time-stamped numeric samples.

Exports
-------
- ``Sample``: dataclass representing a Sample containing a timestamp and a value.
- ``SyntheticSampler``: configurable generator that produces smoothly
  varying samples using a sinusoidal waveform and randomized noise.
- ``ResourceLink``: groups a bandwidth-utilization and latency sampler and
  can produce a sample set for that link.

The module also exposes a ``main`` function that demonstrates simple
periodic sampling when executed as a script.
"""

import csv
import math
import random
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional


@dataclass
class Sample:
    """A single time-stamped numeric sample.

    Attributes
    ----------
    timestamp:
        POSIX timestamp (seconds since epoch, as returned by
        ``datetime.timestamp(datetime.utcnow())``) indicating when the
        sample was produced.
    value:
        Numeric measurement value associated with the timestamp. Semantics
        depend on the sampler that produced the sample (for example,
        percentage for bandwidth utilization or milliseconds for latency).
    """

    timestamp: float
    value: float

@dataclass
class SyntheticSampler:
    """Configurable synthetic numeric sampler.

    The sampler produces values that are a combination of a sinusoidal
    waveform and uniformly randomized noise. Values are clamped between
    ``min_value`` and ``max_value``. Typical use is to simulate smoothly
    changing telemetry such as utilization or latency.

    Parameters
    ----------
    amplitude:
        Peak amplitude of the sinusoidal component.
    phase:
        Phase offset (radians) applied to the sinusoid.
    period:
        Period (in seconds) of the sinusoid. A larger period yields slower
        variation over time.
    offset:
        Constant offset added to the waveform. Useful to keep values
        non-negative or centered around a non-zero mean.
    noise_ratio:
        Blend factor in [0,1] that mixes the deterministic waveform with
        random noise. ``0.0`` yields pure waveform, ``1.0`` yields pure
        noise. Noise amplitude is proportional to ``amplitude``.
    min_value, max_value:
        Optional clamps applied to the produced sample value.
    """

    amplitude   : float = field(default=0.0)
    phase       : float = field(default=0.0)
    period      : float = field(default=1.0)
    offset      : float = field(default=0.0)
    noise_ratio : float = field(default=0.0)
    min_value   : float = field(default=-sys.float_info.max)
    max_value   : float = field(default=sys.float_info.max)

    @classmethod
    def create_random(
        cls, amplitude_scale : float, phase_scale : float, period_scale : float,
        offset_scale : float, noise_ratio : float,
        min_value : Optional[float] = None, max_value : Optional[float] = None
    ) -> 'SyntheticSampler':
        """Create a sampler with randomized parameters.

        The ``*_scale`` parameters control the maximum size of their
        respective randomized parameter. Each generated parameter is the
        product of the scale and a uniform random number in ``[0, 1)``.

        The returned sampler will have an ``offset`` that is at least as
        large as the ``amplitude`` (so that values are more likely to be
        non-negative when amplitude is positive).

        Parameters
        ----------
        amplitude_scale, phase_scale, period_scale, offset_scale:
            Scales used to derive randomized amplitude, phase, period and
            offset respectively.
        noise_ratio:
            Noise blend factor forwarded to the sampler instance.
        min_value, max_value:
            Optional clamps for sample values. If omitted they default to
            the numeric range supported by Python floats.

        Returns
        -------
        SyntheticSampler
            A sampler instance with randomized configuration.
        """

        amplitude = amplitude_scale * random.random()
        phase     = phase_scale     * random.random()
        period    = period_scale    * random.random()
        offset    = offset_scale    * random.random() + amplitude
        if min_value is None: min_value = -sys.float_info.max
        if max_value is None: max_value = sys.float_info.max
        return cls(
            amplitude, phase, period, offset, noise_ratio, min_value, max_value
        )

    def get_sample(self, timestamp : Optional[float] = None) -> Sample:
        """Produce a time-stamped sample based on the sampler configuration.

        The method computes a sinusoidal waveform according to the current
        timestamp, scales it by ``amplitude``, applies the configured
        ``phase`` and ``period``, adds the configured ``offset``, and then
        blends the result with a small random noise scaled by ``amplitude``
        according to ``noise_ratio``.

        If ``timestamp`` is specified as a float, it is assumed a UTC POSIX
        timestamp so sample generated is for that timestamp. If timestamp is
        None, current (now) timestamp is computed and used. Setting timestamp
        is useful to generate long sequences of values for offline analysis,
        plotting, and tests.

        The numeric value is clamped between ``min_value`` and ``max_value``
        and returned together with the timestamp in a ``Sample`` object.

        Returns
        -------
        Sample
            A ``Sample`` containing the UTC POSIX timestamp and the sampled
            numeric value.
        """

        if timestamp is None:
            timestamp = datetime.timestamp(datetime.utcnow())

        waveform = math.sin(2 * math.pi * timestamp / self.period + self.phase)
        waveform *= self.amplitude
        waveform += self.offset

        noise = self.amplitude * random.random()
        value = abs((1.0 - self.noise_ratio) * waveform + self.noise_ratio * noise)

        value = max(value, self.min_value)
        value = min(value, self.max_value)

        return Sample(timestamp, value)

@dataclass
class ResourceLink:
    """Represents a network resource link with associated samplers.

    Attributes
    ----------
    link_name:
        A human readable identifier for the link.
    bw_util_sampler:
        A ``SyntheticSampler`` that produces bandwidth-utilization samples
        (typically percentages).
    latency_sampler:
        A ``SyntheticSampler`` that produces latency samples (for example
        in milliseconds).

    Methods
    -------
    generate_samples(timestamp: Optional[float] = None)
        Returns a dictionary containing a fresh bandwidth-utilization and
        latency ``Sample`` for the link for the provided ``timestamp``.
        If ``timestamp`` is ``None`` the current UTC time is used. The
        timestamp, when provided, must be a POSIX timestamp (seconds since
        the epoch) and will be forwarded to the underlying samplers so the
        two samples share the exact same timestamp.
    """

    link_name: str
    bw_util_sampler: SyntheticSampler
    latency_sampler: SyntheticSampler

    def generate_samples(
        self, timestamp : Optional[float] = None
    ) -> Dict[str, Sample]:
        """Generate a set of samples for this resource link.

        Parameters
        ----------
        timestamp:
            Optional POSIX timestamp (seconds since epoch). When provided
            the samplers will generate values for that timestamp. When
            omitted the current UTC timestamp is used.

        Returns
        -------
        dict
            Dictionary with two keys:
            - ``'bw_util'``: the bandwidth utilization ``Sample``
            - ``'latency'``: the latency ``Sample``

        Notes
        -----
        This method delegates to the configured samplers and forwards the
        provided ``timestamp`` so both returned samples use the same
        timestamp, if not None.
        """

        return {
            'bw_util': self.bw_util_sampler.get_sample(timestamp=timestamp),
            'latency': self.latency_sampler.get_sample(timestamp=timestamp),
        }

def main():
    """Demonstration entry point.

    Creates a sample ``ResourceLink`` with randomized samplers and prints a
    stream of sample sets to stdout at a one second interval. This is useful
    for manual testing or example output when the module is run as a
    script.
    """

    resource_link = ResourceLink(
        link_name='L1',
        bw_util_sampler=SyntheticSampler.create_random(
            amplitude_scale = 25.0,
            phase_scale     = 1e-7,
            period_scale    = 86_400,
            offset_scale    = 25,
            noise_ratio     = 0.05,
            min_value       = 0.0,
            max_value       = 100.0,
        ),
        latency_sampler=SyntheticSampler(
            amplitude_scale = 0.5,
            phase_scale     = 1e-7,
            period_scale    = 60.0,
            offset_scale    = 10.0,
            noise_ratio     = 0.05,
            min_value       = 0.0,
        ),
    )

    print('Settings of samplers:')
    print('  bw_util_sampler=', str(resource_link.bw_util_sampler))
    print('  latency_sampler=', str(resource_link.latency_sampler))

    #print('3 samples for "now":')
    #sampling_interval = 1.0
    #for i in range(3):
    #    link_name = resource_link.link_name
    #    sample_set = resource_link.generate_samples()
    #    MSG = '  [{:s}] SampleSet #{:d}: {:s}'
    #    print(MSG.format(link_name, i+1, str(sample_set)))
    #    time.sleep(sampling_interval)

    # Output CSV file
    csv_filename = 'samples.csv'

    print('20 samples for a fixed timestamp:')
    timestamp = 1760978688.581701
    sampling_interval = 1.0

    with open(csv_filename, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'bw_util', 'latency'])

        for i in range(10):
            link_name = resource_link.link_name
            sample_set = resource_link.generate_samples(timestamp=timestamp)

            MSG = '  [{:s}] SampleSet #{:d}: {:s}'
            print(MSG.format(link_name, i+1, str(sample_set)))

            row = [timestamp, sample_set['bw_util'].value, sample_set['latency'].value]
            writer.writerow(row)

            timestamp += sampling_interval

if __name__ == '__main__':
    main()
