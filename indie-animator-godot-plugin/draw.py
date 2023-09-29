import os
import bpy
from dataclasses import dataclass
import numpy as np
from random import randint
from . utils import *

@dataclass
class Colour:
    r: float
    g: float
    b: float
    a: float

def _set_pixel(image, x, y, colour):
    """
    Set a particular pixel to the colour passed in
    """
    offs = (x + int(y*image.generated_width)) * 4
    image.pixels[offs:offs+4] = colour



def _get_gradient(start, end, steps):
    if steps <= 1:
        return np.reshape(np.array([[start.r, start.g, start.b, start.a]]), [1, 1, 4])
    data = np.array([[(end.r - start.r) * i / (steps - 1) + start.r,
                     (end.g - start.g) * i / (steps - 1) + start.g,
                     (end.b - start.b) * i / (steps - 1) + start.b,
                     (end.a - start.a) * i / (steps - 1) + start.a]
                    for i in range(steps)])

    sub_steps = int(steps / 4)
    start1 = data[0]
    end1 = data[int(sub_steps * 0.5) - 1]
    start2 = end1
    end2 = data[int(sub_steps * 2) - 1]
    start3 = end2
    end3 = data[int(sub_steps * 3.5) - 1]
    start4 = end3
    end4 = data[sub_steps * 4 - 1]

    data1 =  np.array([[(end1[0] - start1[0]) * i / (sub_steps - 1) + start1[0],
                        (end1[1] - start1[1]) * i / (sub_steps - 1) + start1[1],
                        (end1[2] - start1[2]) * i / (sub_steps - 1) + start1[2],
                        (end1[3] - start1[3]) * i / (sub_steps - 1) + start1[3]]
                    for i in range(sub_steps)])

    data2 =  np.array([[(end2[0] - start2[0]) * i / (sub_steps - 1) + start2[0],
                        (end2[1] - start2[1]) * i / (sub_steps - 1) + start2[1],
                        (end2[2] - start2[2]) * i / (sub_steps - 1) + start2[2],
                        (end2[3] - start2[3]) * i / (sub_steps - 1) + start2[3]]
                    for i in range(sub_steps)])

    data3 =  np.array([[(end3[0] - start3[0]) * i / (sub_steps - 1) + start3[0],
                        (end3[1] - start3[1]) * i / (sub_steps - 1) + start3[1],
                        (end3[2] - start3[2]) * i / (sub_steps - 1) + start3[2],
                        (end3[3] - start3[3]) * i / (sub_steps - 1) + start3[3]]
                    for i in range(sub_steps)])

    data4 =  np.array([[(end4[0] - start4[0]) * i / (sub_steps - 1) + start4[0],
                        (end4[1] - start4[1]) * i / (sub_steps - 1) + start4[1],
                        (end4[2] - start4[2]) * i / (sub_steps - 1) + start4[2],
                        (end4[3] - start4[3]) * i / (sub_steps - 1) + start4[3]]
                    for i in range(sub_steps)])

    colors = np.concatenate((data1, data2, data3, data4))
    return np.reshape(colors, [steps, 1, 4])



def _set_gradient_pixel(image, x, y, start_colour, end_colour, width, height):
    """
    Set a group of pixels to the colour passed in
    """
    data = _get_gradient(start_colour, end_colour, height)
    for row in range(height):
        next_colour = data[row].tolist()[0]
        xoff = x
        yoff = y + row
        offs = (xoff + int(yoff*image.generated_width)) * 4
        image.pixels[offs:offs+(4*width)] = next_colour * width


def _clear_image(image, colour):
    """
    Set all pixels to the requested colour
    """
    image.pixels[:] = colour * image.generated_width * image.generated_height


def create_monochrome_gradient_pallet(
    image,
    primary,
    pixel_size
):
    scene = bpy.context.scene

    black = Colour(0, 0, 0, primary.a)
    white = Colour(0.5, 0.5, 0.5, primary.a)
    secondary = Colour(primary.r/6, primary.g/6, primary.b/6, primary.a)
    lowa_black = Colour(black.r, black.g, black.b, primary.a * 0.5)
    lowa_white = Colour(white.r, white.g, white.b, primary.a * 0.5)
    lowa_primary = Colour(primary.r, primary.g, primary.b, primary.a * 0.5)
    lowa_secondary = Colour(secondary.r, secondary.g, secondary.b, secondary.a * 0.5)

    if not scene.allow_transparency:
        primary.a = 1
        secondary.a = 1

    # Lower Left
    add_column(0, 0, image, Colour(0.5, 0.5, 0.5, 1), Colour(0.15, 0.15, 0.15, 1), pixel_size)
    add_column(0, 2, image, primary, secondary, pixel_size)
    add_column(0, 4, image, secondary, primary, pixel_size)
    add_column(0, 6, image, primary, white, pixel_size)
    # Upper Left
    add_column(8, 0, image, Colour(0.15, 0.15, 0.15, 1), Colour(0, 0, 0, 1), pixel_size)
    add_column(8, 2, image, secondary, primary, pixel_size)
    add_column(8, 4, image, primary, secondary, pixel_size)
    add_column(8, 6, image, white, secondary, pixel_size)
    # Upper Right
    add_column(8, 8, image, Colour(0.15, 0.15, 0.15, 1), Colour(0, 0, 0, 1), pixel_size)
    add_column(8, 10, image, secondary, black, pixel_size)
    add_column(8, 12, image, primary, black, pixel_size)
    add_column(8, 14, image, white, primary, pixel_size)
    # Lower Right
    if scene.allow_transparency:
        add_column(0, 8, image, Colour(0.15, 0.15, 0.15, 1), Colour(0, 0, 0, 1), pixel_size)
        add_column(0, 10, image, lowa_secondary, lowa_black, pixel_size)
        add_column(0, 12, image, lowa_primary, lowa_black, pixel_size)
        add_column(0, 14, image, lowa_white, lowa_primary, pixel_size)
    else:
        add_column(0, 8, image, Colour(0.15, 0.15, 0.15, 1), Colour(0, 0, 0, 1), pixel_size)
        add_column(0, 10, image, secondary, white, pixel_size)
        add_column(0, 12, image, primary, white, pixel_size)
        add_column(0, 14, image, white, primary, pixel_size)

def create_single_gradient_pallet(
    image,
    primary,
    secondary,
    pixel_size
):
    scene = bpy.context.scene

    black = Colour(0, 0, 0, primary.a)
    white = Colour(0.5, 0.5, 0.5, primary.a)
    lowa_black = Colour(black.r, black.g, black.b, primary.a * 0.5)
    lowa_white = Colour(white.r, white.g, white.b, primary.a * 0.5)
    lowa_primary = Colour(primary.r, primary.g, primary.b, primary.a * 0.5)
    lowa_secondary = Colour(secondary.r, secondary.g, secondary.b, primary.a * 0.5)

    if not scene.allow_transparency:
        primary.a = 1
        secondary.a = 1

    # Lower Left
    add_column(0, 0, image, Colour(0.5, 0.5, 0.5, 1), Colour(0.15, 0.15, 0.15, 1), pixel_size)
    add_column(0, 2, image, primary, secondary, pixel_size)
    add_column(0, 4, image, secondary, primary, pixel_size)
    add_column(0, 6, image, primary, white, pixel_size)
    # Upper Left
    add_column(8, 0, image, Colour(0.15, 0.15, 0.15, 1), Colour(0, 0, 0, 1), pixel_size)
    add_column(8, 2, image, secondary, primary, pixel_size)
    add_column(8, 4, image, primary, secondary, pixel_size)
    add_column(8, 6, image, white, secondary, pixel_size)
    # Upper Right
    add_column(8, 8, image, Colour(0.15, 0.15, 0.15, 1), Colour(0, 0, 0, 1), pixel_size)
    add_column(8, 10, image, secondary, black, pixel_size)
    add_column(8, 12, image, primary, black, pixel_size)
    add_column(8, 14, image, white, primary, pixel_size)
    # Lower Right
    if scene.allow_transparency:
        add_column(0, 8, image, Colour(0.15, 0.15, 0.15, 1), Colour(0, 0, 0, 1), pixel_size)
        add_column(0, 10, image, lowa_secondary, lowa_black, pixel_size)
        add_column(0, 12, image, lowa_primary, lowa_black, pixel_size)
        add_column(0, 14, image, lowa_white, lowa_primary, pixel_size)
    else:
        add_column(0, 8, image, Colour(0.15, 0.15, 0.15, 1), Colour(0, 0, 0, 1), pixel_size)
        add_column(0, 10, image, secondary, white, pixel_size)
        add_column(0, 12, image, primary, white, pixel_size)
        add_column(0, 14, image, white, primary, pixel_size)

def create_double_gradient_pallet(
    image,
    primary,
    secondary,
    third,
    pixel_size
):
    scene = bpy.context.scene

    black = Colour(0, 0, 0, primary.a)
    white = Colour(0.5, 0.5, 0.5, primary.a)
    lowa_black = Colour(black.r, black.g, black.b, primary.a * 0.5)
    lowa_primary = Colour(primary.r, primary.g, primary.b, primary.a * 0.5)
    lowa_secondary = Colour(secondary.r, secondary.g, secondary.b, primary.a * 0.5)
    lowa_third = Colour(third.r, third.g, third.b, primary.a * 0.5)

    if not scene.allow_transparency:
        primary.a = 1
        secondary.a = 1
        third.a = 1

    # Lower Left
    add_column(0, 0, image, Colour(0.5, 0.5, 0.5, 1), Colour(0.15, 0.15, 0.15, 1), pixel_size)
    add_column(0, 2, image, third, secondary, pixel_size)
    add_column(0, 4, image, primary, third, pixel_size)
    add_column(0, 6, image, secondary, primary, pixel_size)
    # Upper Left
    add_column(8, 0, image, Colour(0.15, 0.15, 0.15, 1), Colour(0, 0, 0, 1), pixel_size)
    add_column(8, 2, image, secondary, primary, pixel_size)
    add_column(8, 4, image, third, secondary, pixel_size)
    add_column(8, 6, image, primary, third, pixel_size)
    # Upper Right
    add_column(8, 8, image, Colour(0.15, 0.15, 0.15, 1), Colour(0, 0, 0, 1), pixel_size)
    add_column(8, 10, image, secondary, black, pixel_size)
    add_column(8, 12, image, third, black, pixel_size)
    add_column(8, 14, image, primary, black, pixel_size)
    # Lower Right
    if scene.allow_transparency:
        add_column(0, 8, image, Colour(0.15, 0.15, 0.15, 1), Colour(0, 0, 0, 1), pixel_size)
        add_column(0, 10, image, lowa_secondary, lowa_black, pixel_size)
        add_column(0, 12, image, lowa_third, lowa_black, pixel_size)
        add_column(0, 14, image, lowa_primary, lowa_black, pixel_size)
    else:
        add_column(0, 8, image, Colour(0.15, 0.15, 0.15, 1), Colour(0, 0, 0, 1), pixel_size)
        add_column(0, 10, image, secondary, white, pixel_size)
        add_column(0, 12, image, third, white, pixel_size)
        add_column(0, 14, image, primary, white, pixel_size)

def get_pixel_colour(image, x, y):
    colour = image.pixels[(y * image.generated_width + x) * 4 : (y * image.generated_width + x + 1) * 4]
    return Colour(colour[0], colour[1], colour[2], colour[3])

def add_column(
    row,
    column,
    image,
    start_colour,
    end_colour,
    pixel_size
):
    height = pixel_size * 8

    # Draw the second column as a full gradient from dark to light
    _set_gradient_pixel(
        image,
        (column * pixel_size) + pixel_size,
        row * pixel_size,
        start_colour,
        end_colour,
        pixel_size,
        pixel_size * 8)

    # Get the corresponding colours from the gradient to fill in the full pixels in the first column
    half_pixel = int(pixel_size/2)
    qrtr_pixel = int(pixel_size/4)
    for i in range(8):
        # Make sure the colour you pick is the darkest one so for the bottom colours we pick the pixel at
        # the bottom and the top ones we pick the one at the top
        if i >= 4:
            colour_start = get_pixel_colour(image, (column + 1) * pixel_size + half_pixel, (row * pixel_size) + (i + 1) * pixel_size - 1)
        else:
            colour_start = get_pixel_colour(image, (column + 1) * pixel_size + half_pixel, (row * pixel_size) + i * pixel_size)
        _set_gradient_pixel(
                image,
                column * pixel_size,
                (row * pixel_size) + (i * pixel_size),
                colour_start,
                colour_start,
                pixel_size,
                pixel_size)


def save_image(image, image_name):
    image.file_format = 'PNG'
    #image.colorspace_settings.name = 'sRGB'
    image.filepath_raw = os.path.dirname(bpy.data.filepath) + f"/{image_name}.png"
    image.update()
    image.save()
    return image


def create_gradient_pallet(
    image_name,
    primary_colour,
    secondary_colours = [],
    pixel_size = 1
):
    """
    Generate a pallet with a gradient for each colour and apply to an image.  The primary colour
    get 2 rows of options, secondary colours gets 2 rows and 2 rows for standard white/black/grey
    """
    if not bpy.data.filepath:
        info("Please save your blend file first")
        return None

    if not primary_colour:
        info("Primary colour required")
        return None

    valid_pixel_sizes = [1, 8, 16, 32, 64]
    if pixel_size not in valid_pixel_sizes:
        info(f"Allowed pixel sizes: {valid_pixel_sizes}")
        return None

    image_name = image_name.lower()
    image_width = 8 * pixel_size * 2
    image_height = image_width

    image = bpy.data.images.get(image_name)
    if not image:
        image = bpy.data.images.new(
            image_name,
            width=image_width,
            height=image_height,
            alpha=True,
            float_buffer=True)

    elif image.generated_width != image_width or image.generated_height != image_height:
        bpy.data.images.remove(bpy.data.images[image_name])
        image = bpy.data.images.new(
            image_name,
            width=image_width,
            height=image_height,
            alpha=True,
            float_buffer=True)

    _clear_image(image, [0, 0, 0, 1.0])

    primary_colour = Colour(primary_colour[0], primary_colour[1], primary_colour[2], primary_colour[3])

    # Based on the number of colours we are dealing with create the appropriate colour pallette
    num_secondary_colurs = len(secondary_colours)
    if not secondary_colours:
        create_monochrome_gradient_pallet(image, primary_colour, pixel_size)
    elif num_secondary_colurs == 1:
        secondary_colour = Colour(secondary_colours[0][0], secondary_colours[0][1], secondary_colours[0][2], secondary_colours[0][3])
        create_single_gradient_pallet(image, primary_colour, secondary_colour, pixel_size)
    else:
        secondary_colour = Colour(secondary_colours[0][0], secondary_colours[0][1], secondary_colours[0][2], secondary_colours[0][3])
        third_colour = Colour(secondary_colours[1][0], secondary_colours[1][1], secondary_colours[1][2], secondary_colours[1][3])
        create_double_gradient_pallet(image, primary_colour, secondary_colour, third_colour, pixel_size)

    return save_image(image, image_name)

def has_alpha(ob):
    return False
    for slot in ob.material_slots:
        if slot.material and slot.material.node_tree:
            for node in slot.material.node_tree.nodes:
                if node.type == 'TEX_IMAGE' and node.image.name != "Render Result" and _has_alpha(node.image):
                    return True
    return False

def _has_alpha(image):
    width = image.generated_width
    height = image.generated_height

    # Check the four corners for a non full alpha
    start = 0
    if image.pixels[start:start + 4][3] < 1:
        return True
    start = (width - 1) * 4
    if image.pixels[start:start + 4][3] < 1:
        return True
    start = (width * int(height/2) - 1) * 4
    if image.pixels[start:start + 4][3] < 1:
        return True
    start = ((width * int(height/2) - 1) + (width - 1)) * 4
    if image.pixels[start:start + 4][3] < 1:
        return True
    return False
