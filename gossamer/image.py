"""
Compare screenshots taken via the webdriver.
"""

# Copyright (c) 2013 contributors; see AUTHORS.
# Licensed under the Apache License, Version 2.0
# https://www.apache.org/licenses/LICENSE-2.0

import math
import operator

try:
    # Pillow
    from PIL import Image
    from PIL import ImageChops
except ImportError: # pragma: no cover
    # PIL
    try:
        import Image # pylint: disable=F0401
        import ImageChops # pylint: disable=F0401
    except ImportError:
        raise ImportError('Could not import Pillow or PIL')

from gossamer import util, exc

def allowance(browser):
    """
    Our image diffs below give some false alarms of diffs... The values
    below are rmsdiff values for 100%-same ImageChops histograms (i.e.,
    ImageChops' bounding box method showed no difference), and for
    trivial rendering differences, e.g., a pixel within a button gradient
    differing, or rendered text differing very slightly, we add a slight
    allowance.
    """
    margin = 1.001
    margins = {
        'default': 572.4334022399462*margin,
        'chrome': 572.4334022399462*margin,
        'firefox': 957.864291014*margin
    }
    try:
        return margins[browser]
    except KeyError:
        return margins['default']


def images_identical(path1, path2, margin=None):
    """
    Hacky test of images being identical. PIL can show incorrect diffs.
    """
    util.log.debug('images_identical: %s, %s', path1, path2)

    im1 = Image.open(path1)
    im2 = Image.open(path2)
    if ImageChops.difference(im1, im2).getbbox() is None:
        util.log.debug('images_identical: bounding box ok')
        identical = True
    else:
        rmsdiff = _rmsdiff_2011(im1, im2)
        margin = margin or 0
        if rmsdiff <= margin:
            util.log.debug('images_identical: rmsdiff %s ok' % rmsdiff)
            identical = True
        else:
            util.log.debug('images_identical: rmsdiff %s failed' % rmsdiff)
            identical = False
    return identical


def image_diff(path1, path2, outpath, diffcolor):
    """
    Generate a diff image on a screenshot which has failed
    :func:`.images_identical`.
    """
    im1 = Image.open(path1)
    im2 = Image.open(path2)
    rmsdiff = _rmsdiff_2011(im1, im2)

    pix1 = im1.load()
    pix2 = im2.load()

    if im1.mode != im2.mode:
        raise exc.TestError(
            'Different pixel modes between %r and %r' % \
            (path1, path2)
        )
    if im1.size != im2.size:
        raise exc.TestError(
            'Different dimensions between %r (%r) and %r (%r)' % \
            (path1, im1.size, path2, im2.size)
        )

    mode = im1.mode
    if mode == '1':
        value = 255
    elif mode == 'L':
        value = 255
    elif mode == 'RGB':
        value = diffcolor
    elif mode == 'RGBA':
        value = diffcolor + (255,)
    elif mode == 'P':
        raise NotImplementedError('Need to look up nearest palette color')
    else:
        raise NotImplementedError('Unexpected PNG mode')

    width, height = im1.size
    for y in range(height):
        for x in range(width):
            if pix1[x, y] != pix2[x, y]:
                pix2[x, y] = value

    im2.save(outpath)
    return (rmsdiff, width, height)


def _rmsdiff_2011(im1, im2):
    "Calculate the root-mean-square difference between two images"
    h = ImageChops.difference(im1, im2).histogram()
    rms = math.sqrt(
        reduce(
            operator.add,
            map(lambda h, i: h*(i**2), h, range(len(h))) # pylint: disable=W0110,W0141
        ) / (float(im1.size[0]) * im1.size[1])
    )
    return rms

