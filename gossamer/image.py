"""
Compare screenshots taken via the webdriver.
"""

# Copyright (c) 2013 contributors; see AUTHORS.
# Licensed under the Apache License, Version 2.0
# https://www.apache.org/licenses/LICENSE-2.0

import math

try:
    # Pillow
    from PIL import Image
    from PIL import ImageChops
except ImportError: # pragma: no cover
    # PIL
    try:
        import Image
        import ImageChops
    except ImportError:
        raise ImportError('Could not import Pillow or PIL')

from gossamer import util, exc

def allowance(browser):
    """
    Our image diffs below give some false alarms of diffs. For the browser
    Chrome, which takes screenshots limited to screensize, a value of at least
    573 is always seen. For Firefox, which takes screenshots the width of
    the actual screensize and the height of the document, 958.
    """
    margins = {'default': 573, 'chrome': 573, 'firefox': 958}
    try:
        return margins[browser]
    except KeyError:
        return margins['default']


def images_identical(path1, path2, margin=None):
    """
    Hacky test of images being identical. PIL can show incorrect diffs.
    """
    margin = margin or 0
    im1 = Image.open(path1)
    im2 = Image.open(path2)
    rmsdiff = _rmsdiff_2011(im1, im2)
    if rmsdiff <= margin:
        return True
    else:
        return False


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

    for y in xrange(height):
        for x in xrange(width):
            if pix1[x, y] != pix2[x, y]:
                pix2[x, y] = value
    im2.save(outpath)

    return (rmsdiff, width, height)


def _rmsdiff_2011(im1, im2):
    "Calculate the root-mean-square difference between two images"
    diff = ImageChops.difference(im1, im2)
    h = diff.histogram()
    sq = (value * (idx ** 2) for idx, value in enumerate(h))
    sum_of_squares = sum(sq)
    rms = math.sqrt(sum_of_squares / float(im1.size[0] * im1.size[1]))
    util.log.debug('rmsdiff: %s', rms)
    return rms
