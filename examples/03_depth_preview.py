#!/usr/bin/env python3

import cv2
import depthai as dai
import numpy as np

# Closer-in minimum depth, disparity range is doubled (from 95 to 190):
extended_disparity = False
# Better accuracy for longer distance, fractional disparity 32-levels:
subpixel = False
# Better handling for occlusions:
lr_check = False

# Start defining a pipeline
pipeline = dai.Pipeline()

# Define sources and outputs
monoLeft = pipeline.createMonoCamera()
monoRight = pipeline.createMonoCamera()
depth = pipeline.createStereoDepth()
xout = pipeline.createXLinkOut()

xout.setStreamName("disparity")

# Properties
monoLeft.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
monoLeft.setBoardSocket(dai.CameraBoardSocket.LEFT)
monoRight.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
monoRight.setBoardSocket(dai.CameraBoardSocket.RIGHT)

# Create a node that will produce the depth map (using disparity output as it's easier to visualize depth this way)
depth.setConfidenceThreshold(200)
# Options: MEDIAN_OFF, KERNEL_3x3, KERNEL_5x5, KERNEL_7x7 (default)
depth.setMedianFilter(dai.StereoDepthProperties.MedianFilter.KERNEL_7x7)
depth.setLeftRightCheck(lr_check)

# Normal disparity values range from 0..95, will be used for normalization
max_disparity = 95

if extended_disparity: max_disparity *= 2 # Double the range
depth.setExtendedDisparity(extended_disparity)

if subpixel: max_disparity *= 32 # 5 fractional bits, x32
depth.setSubpixel(subpixel)

# When we get disparity to the host, we will multiply all values with the multiplier
# for better visualization
multiplier = 255 / max_disparity

# Linking
monoLeft.out.link(depth.left)
monoRight.out.link(depth.right)
depth.disparity.link(xout.input)

# Pipeline is defined, now we can connect to the device
with dai.Device(pipeline) as device:
    # Start pipeline
    device.startPipeline()

    # Output queue will be used to get the disparity frames from the outputs defined above
    q = device.getOutputQueue(name="disparity", maxSize=4, blocking=False)
    while True:
        inDepth = q.get()  # blocking call, will wait until a new data has arrived
        frame = inDepth.getFrame()
        frame = (frame*multiplier).astype(np.uint8)

        cv2.imshow("disparity", frame)

        # Available color maps: https://docs.opencv.org/3.4/d3/d50/group__imgproc__colormap.html
        frame = cv2.applyColorMap(frame, cv2.COLORMAP_JET)
        cv2.imshow("disparity_color", frame)

        if cv2.waitKey(1) == ord('q'):
            break
