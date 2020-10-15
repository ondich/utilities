#!/usr/bin/env python3
'''
    greenscreen-helper.py
    Jeff Ondich, 31 Aug 2020

    I have a greenscreen in a picture frame on the wall behind me
    when I'm in my home office for Zoom meetings and teaching.
    I want to be able to put arbitrary photos and text images in the
    frame using Zoom's greenscreen background, but that means the desired
    image has to be properly scaled and translated and put into a larger
    image so the whole image will appear in the frame.

    The most important functions are 

    Color names: https://imagemagick.org/script/color.php
'''

import sys
import os
import subprocess
import argparse

DEBUG = True

# These hard-coded values are specific to the layout of my office, the positioning
# of my webcam, the placement of my greenscreen on the wall behind me, etc.
CANVAS_WIDTH = 1280
CANVAS_HEIGHT = 720
GREENSCREEN_LEFT = 772
GREENSCREEN_TOP = 42
GREENSCREEN_WIDTH = 422
GREENSCREEN_HEIGHT = 318

# These values can be retained even if I change my office layout.
FAT_FRAME_THICKNESS = 0.05
FAT_GREENSCREEN_LEFT = int(float(GREENSCREEN_LEFT) - float(GREENSCREEN_WIDTH) * FAT_FRAME_THICKNESS)
FAT_GREENSCREEN_TOP = int(float(GREENSCREEN_TOP) - float(GREENSCREEN_HEIGHT) * FAT_FRAME_THICKNESS)
FAT_GREENSCREEN_WIDTH = int(float(GREENSCREEN_WIDTH) * (1.0 + 2 * FAT_FRAME_THICKNESS))
FAT_GREENSCREEN_HEIGHT = int(float(GREENSCREEN_HEIGHT) * (1.0 + 2 * FAT_FRAME_THICKNESS))

def debug_print(message):
    if DEBUG:
        print(message, file=sys.stderr)

def make_solid_color_image(width, height, color, output_image):
    if '#' == color[:1]:
        color_flag = f'xc:{color}'
    else:
        color_flag = f'canvas:{color}'
    command = f'convert -size {width}x{height} {color_flag} "{output_image}"'
    debug_print(command)
    os.system(command)

def overlay_on_image(x, y, background_image, overlay_image, output_image):
    command = f'composite -compose atop -geometry +{x}+{y} {overlay_image} {background_image} {output_image}'
    debug_print(command)
    os.system(command)

def overlay_video_on_image(left, top, width, height, background_image, overlay_video, output_video):
    command = f'ffmpeg -loop 1 -i {background_image} -vf "movie={overlay_video},scale={width}:{height}[inner];[in][inner]overlay={left}:{int(top)}:shortest=1[out]" -y {output_video}'
    debug_print(command)
    os.system(command)

def scale_image(scale_percent, input_image, output_image):
    command = f'convert -scale {scale_percent}% "{input_image}" "{output_image}"'
    debug_print(command)
    os.system(command)

def resize_image(new_width, new_height, input_image, output_image):
    command = f'convert "{input_image}" -resize {new_width}x{new_height}\\! "{output_image}"'
    debug_print(command)
    os.system(command)

def image_size(input_image):
    result = subprocess.run(['identify', '-format', '%w %h', input_image], stdout=subprocess.PIPE).stdout.decode('utf-8')
    width, height = map(int, result.split())
    return width, height

def video_size(input_video):
    result = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of', 'csv=s=x:p=0', input_video], stdout=subprocess.PIPE).stdout.decode('utf-8')
    width, height = map(int, result.split('x'))
    return width, height

def make_caption_image(caption, width, height, background_color, text_color, font, output_image):
    command = f'convert -background "{background_color}" -fill "{text_color}" -font "{font}" -size {width}x{height} caption:"{caption}" "{output_image}"'
    debug_print(command)
    os.system(command)

def invert_colors(input_image, output_image):
    command = f'convert {input_image} -channel RGB -negate {output_image}'
    os.system(command)

def make_canvas(color, output_image, include_greenscreen_frame=False):
    if include_greenscreen_frame:
        base_name = output_image[:output_image.rfind('.')]
        extension = output_image[output_image.rfind('.') + 1:]
        blank_canvas_image = f'{base_name}-background.{extension}'
        greenscreen_image = f'{base_name}-greenscreen.{extension}'
        fat_greenscreen_image = f'{base_name}-fat-greenscreen.{extension}'
        intermediate_image = f'{base_name}-intermediate.{extension}'
        make_solid_color_image(CANVAS_WIDTH, CANVAS_HEIGHT, color, blank_canvas_image)
        make_solid_color_image(GREENSCREEN_WIDTH, GREENSCREEN_HEIGHT, 'orange', greenscreen_image)
        make_solid_color_image(FAT_GREENSCREEN_WIDTH, FAT_GREENSCREEN_HEIGHT, 'red', fat_greenscreen_image)
        overlay_on_image(FAT_GREENSCREEN_LEFT, FAT_GREENSCREEN_TOP, blank_canvas_image, fat_greenscreen_image, intermediate_image)
        overlay_on_image(GREENSCREEN_LEFT, GREENSCREEN_TOP, intermediate_image, greenscreen_image, output_image)
        command = f'rm "{blank_canvas_image}" "{greenscreen_image}" "{fat_greenscreen_image}" "{intermediate_image}"'
        os.system(command)
    else:
        make_solid_color_image(CANVAS_WIDTH, CANVAS_HEIGHT, color, output_image)

def greenscreen_rect(screen_width, screen_height):
    left = int(float(GREENSCREEN_LEFT) * float(screen_width) / float(CANVAS_WIDTH))
    top = int(float(GREENSCREEN_TOP) * float(screen_height) / float(CANVAS_HEIGHT))
    width = int(float(GREENSCREEN_WIDTH) * float(screen_width) / float(CANVAS_WIDTH))
    height = int(float(GREENSCREEN_HEIGHT) * float(screen_height) / float(CANVAS_HEIGHT))
    return left, top, width, height

def fat_greenscreen_rect(screen_width, screen_height):
    left = int(float(FAT_GREENSCREEN_LEFT) * float(screen_width) / float(CANVAS_WIDTH))
    top = int(float(FAT_GREENSCREEN_TOP) * float(screen_height) / float(CANVAS_HEIGHT))
    width = int(float(FAT_GREENSCREEN_WIDTH) * float(screen_width) / float(CANVAS_WIDTH))
    height = int(float(FAT_GREENSCREEN_HEIGHT) * float(screen_height) / float(CANVAS_HEIGHT))
    return left, top, width, height

def greenscreen_overlay_rect_for_image(image_width, image_height, screen_width, screen_height):
    gs_left, gs_top, gs_width, gs_height = fat_greenscreen_rect(screen_width, screen_height)
    debug_print(f'FGS: {gs_left}, {gs_top}, {gs_width}x{gs_height}')
    gs_aspect_ratio = float(gs_height) / float(gs_width)
    debug_print(f'FGS AR: {gs_aspect_ratio}')
    image_aspect_ratio = float(image_height) / float(image_width)
    debug_print(f'Image AR: {image_aspect_ratio}')
    if float(abs(gs_aspect_ratio - image_aspect_ratio)) / gs_aspect_ratio < 0.1:
        debug_print('Using fat greenscreen')
        left, top, width, height =  gs_left, gs_top, gs_width, gs_height
    elif gs_aspect_ratio > image_aspect_ratio:
        debug_print('Using full width')
        left = gs_left
        width = gs_width
        height = int(image_aspect_ratio * float(width))
        top = int(gs_top + (gs_height - height) / 2)
    else:
        debug_print('Using full height')
        height = gs_height
        top = gs_top
        width = int(float(height) / image_aspect_ratio)
        left = int(gs_left + (gs_width - width) / 2)
    return left, top, width, height

def caption_to_greenscreen(args):
    output_base_name = args.output_image[:args.output_image.rfind('.')]
    output_extension = args.output_image[args.output_image.rfind('.') + 1:]
    background_image = f'{output_base_name}-background.{output_extension}'
    caption_image = f'{output_base_name}-caption.{output_extension}'
    make_solid_color_image(CANVAS_WIDTH, CANVAS_HEIGHT, args.background, background_image)
    gs_left, gs_top, gs_width, gs_height = greenscreen_rect(CANVAS_WIDTH, CANVAS_HEIGHT)
    make_caption_image(args.caption, gs_width, gs_height, args.background, args.textcolor, args.font, caption_image)
    overlay_on_image(gs_left, gs_top, background_image, caption_image, args.output_image)
    command = f'rm "{background_image}" "{caption_image}"'
    os.system(command)

def image_to_greenscreen(args):
    input_base_name = args.input_image[:args.input_image.rfind('.')]
    input_extension = args.input_image[args.input_image.rfind('.') + 1:]
    background_image = f'{input_base_name}-background.{input_extension}'
    resized_image = f'{input_base_name}-resized.{input_extension}'
    make_canvas(args.background, background_image)
    image_width, image_height = image_size(args.input_image)
    left, top, width, height = greenscreen_overlay_rect_for_image(image_width, image_height, CANVAS_WIDTH, CANVAS_HEIGHT) 
    resize_image(width, height, args.input_image, resized_image)
    overlay_on_image(left, top, background_image, resized_image, args.output_image)
    command = f'rm "{background_image}" "{resized_image}"'
    os.system(command)

def video_to_greenscreen(args):
    input_base_name = args.input_video[:args.input_video.rfind('.')]
    input_extension = args.input_video[args.input_video.rfind('.') + 1:]
    background_image = f'{input_base_name}-background.jpg'
    make_canvas(args.background, background_image, True)
    video_width, video_height = video_size(args.input_video)
    left, top, width, height = greenscreen_overlay_rect_for_image(video_width, video_height, CANVAS_WIDTH, CANVAS_HEIGHT) 
    overlay_video_on_image(left, top, width, height, background_image, args.input_video, args.output_video)
    #command = f'rm "{background_image}" "{args.output_video}"'
    #os.system(command)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', action='version', version='1.0.0')
    subparsers = parser.add_subparsers()

    image_parser = subparsers.add_parser('image')
    image_parser.add_argument('input_image', help='name of the image to be placed on the greenscreen')
    image_parser.add_argument('output_image', help='name of the output image')
    image_parser.add_argument('--background', default='black', help='background color')
    image_parser.set_defaults(func=image_to_greenscreen)

    caption_parser = subparsers.add_parser('caption')
    caption_parser.add_argument('caption', help='text of the desired caption')
    caption_parser.add_argument('output_image', help='name of the output image')
    caption_parser.add_argument('--background', default='black', help='background color')
    caption_parser.add_argument('--textcolor', default='white', help='text color')
    caption_parser.add_argument('--font', default='Helvetica', help='font')
    caption_parser.set_defaults(func=caption_to_greenscreen)

    video_parser = subparsers.add_parser('video')
    video_parser.add_argument('input_video', help='name of the input video')
    video_parser.add_argument('output_video', help='name of the output video')
    video_parser.add_argument('--background', default='black', help='background color')
    video_parser.set_defaults(func=video_to_greenscreen)

    args = parser.parse_args()
    args.func(args)

