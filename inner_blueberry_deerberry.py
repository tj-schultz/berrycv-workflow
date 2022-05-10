#!/usr/bin/env python3

"""
Name: inner_blueberry_deerberry.py
Description: blueberry/deerberry workflow for inner fruit feature extraction
Author: TJ Schultz
Date: 9/9/2021
"""
import argparse
import sys
import os.path
from datetime import datetime as dt
import re
import time

from plantcv import plantcv as pcv
import berrycv as bcv
import cv2
import numpy as np

## program options
pcv.params.debug = "none"


## get the working directory
wd = os.getcwd()
    
## options for plantcv workflow -- add arguments for plantcv-workflow.py compatibility
def options():
    parser = argparse.ArgumentParser(description="Imaging processing with PlantCV.")
    parser.add_argument("-i", "--image", help="Input image file.", required=True)
    parser.add_argument("-r","--result", help="Result file.", required= True )
    parser.add_argument("-o", "--outdir", help="Output directory for image files.", required=False)
    parser.add_argument("-w","--writeimg", help="Write out images.", default=False, action="store_true")
    parser.add_argument("-D", "--debug", help="Turn on debug, prints intermediate images.")
    args = parser.parse_args()
    return args

## returns a binary mask of the image for use in object detection
def generate_mask(img):
    
    ## first isolate the saturation channel, threshold it
    s = pcv.rgb2gray_hsv(rgb_img=img, channel='s')
    s_th = pcv.threshold.triangle(gray_img=s, max_value=255, object_type='light', xstep=20)
    
    
    ## then isolate the lightness channel, threshold it
    l = pcv.rgb2gray_lab(rgb_img=img, channel='l')
    l_th = pcv.threshold.triangle(gray_img=l, max_value=255, object_type='dark')

    ## blur the saturation and lightness image to soften small features
    s_th_blur = pcv.median_blur(gray_img=s_th, ksize=5)
    l_th_blur = pcv.median_blur(gray_img=l_th, ksize=5)
    
    ## 'logical or' the images to create a joined binary image
    ls = pcv.logical_or(s_th_blur, l_th_blur)
    
    ## pass a filled image back after logical-or joining the inverted fill
    ls_fill = pcv.fill(bin_img=ls, size=1000)
    
    ls_fill_inv = pcv.fill(bin_img=pcv.invert(ls_fill), size=1000)
    
    ls_or_final = pcv.logical_or(pcv.invert(ls_fill_inv), ls_fill)
    return ls_or_final

## main
def main():
    ## read workflow JSON
    data_JSON = bcv.readJSONconfig(os.path.join(wd, 'config/config.json'))
    
    #+ get options list
    args = options()

    ## set debug
    pcv.params.debug = args.debug

    ## read image using args flag
    filename = args.image
    sample_img = bcv.read_image(filename)
    
    ## fix the name to remove the full path for output
    name = filename[len(wd)+1:]

    ## if not bad image, sample_img and analyze
    if not len(sample_img) == 0:

        ## output filename
        print("Filename: %s" % name)

        ## create mask
        mask = generate_mask(sample_img)
        
        ## identify objects -- should be only one object
        id_objects,obj_hierarchy = pcv.find_objects(img=sample_img, mask=mask)
                
        ## for each object -- though there should be one per sample photo
        for o in range(len(id_objects)):
            
            ## set the key to the shortened filename
            key = name
            
            ## analyze object, color
            analyze_obj_img = pcv.analyze_object(img=sample_img, obj=id_objects[o], mask=mask, label=key)
            analyze_color_img = pcv.analyze_color(rgb_img=sample_img, mask=mask, label=key, colorspaces='hsv')

            ## write analysis image to plots
            pcv.print_image(analyze_color_img, os.path.join('plots', key))

            """
            ## blue img before using naive baysian classifier
            blur_img = pcv.gaussian_blur(img=sample_img, ksize=(17, 17), sigma_x=0, sigma_y=None)
            
            experimental -- detect areas of features in the photo using naive bayesian model"""
            """
            ## create naive bayesian mask list
            nb_masks = pcv.naive_bayes_classifier(rgb_img=blur_img, pdf_file=data_JSON["naive_bayesian_filename"])
            
            ## get area of each feature
            red_pulp_area = np.count_nonzero(nb_masks['red pulp'])
            green_pulp_area = np.count_nonzero(nb_masks['green pulp'])
            white_pulp_area = np.count_nonzero(nb_masks['white pulp'])
            seeds_area = np.count_nonzero(nb_masks['seeds'])
            
            
            
            ## add observations to the output JSON
            pcv.outputs.add_observation(sample=key, variable='red_pulp_area', trait='area of red pulp',
                                method='count of pixels', scale='pixels', datatype=int,
                                value=red_pulp_area, label=key)
            pcv.outputs.add_observation(sample=key, variable='green_pulp_area', trait='area of green pulp',
                                method='count of pixels', scale='pixels', datatype=int,
                                value=green_pulp_area, label=key)
            pcv.outputs.add_observation(sample=key, variable='white_pulp_area', trait='area of white pulp',
                                method='count of pixels', scale='pixels', datatype=int,
                                value=white_pulp_area, label=key)
            pcv.outputs.add_observation(sample=key, variable='seeds_area', trait='area of seeds',
                                    method='count of pixels', scale='pixels', datatype=int,
                                    value=seeds_area, label=key)
            
            ## create color list from JSON file -- this is for visualizing the color masks
            RGWS_COLORS = list(data_JSON["classes"][0].values())
            
            
            nb_masks['red pulp'] = pcv.logical_and(crop_mask,  nb_masks['red pulp'])
            nb_masks['green pulp'] = pcv.logical_and(crop_mask,  nb_masks['green pulp'])
            nb_masks['white pulp'] = pcv.logical_and(crop_mask,  nb_masks['white pulp'])
            nb_masks['seeds'] = pcv.logical_and(crop_mask,  nb_masks['seeds'])
            """
            """colored_img = pcv.visualize.colorize_masks(masks=[nb_masks['background'], nb_masks['red pulp'], nb_masks['green pulp'],\
                                                              nb_masks['white pulp'], nb_masks['seeds']],\
                                                       colors=RGWS_COLORS)
            """
            
        pcv.outputs.save_results(filename=args.result, outformat="json")

if __name__ == '__main__':
    main()


        
        
