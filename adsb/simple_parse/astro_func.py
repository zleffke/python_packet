#!/usr/bin/env python3
##################################################
# Title: Map Functions
# Author: Zachary James Leffke
# Description: Calculate bearing, distance, etc. from lat/lon
# Generated: December 20, 2013
##################################################

from math import *
import numpy as np
import scipy as sp

R_e = 6378.137 				#Earth Radius, in kilometers
e_e = 0.081819221456	#Eccentricity of Earth
deg2rad = pi / 180
rad2deg = 180 / pi

def LLH_To_ECEF(lat, lon, h):
	#INPUT:
	#	h   - height above ellipsoid (MSL), km
	#	lat - geodetic latitude, in radians
	#	lon - longitude, in radians
    C_e = R_e / sqrt(1 - pow(e_e, 2) * pow(sin(lat),2))
    S_e = C_e * (1 - pow(e_e, 2))
    r_i = (C_e + h) * cos(lat) * cos(lon)
    r_j = (C_e + h) * cos(lat) * sin(lon)
    r_k = (S_e + h) * sin(lat)
    return r_i, r_j, r_k

def RAZEL(lat1, lon1, h1, lat2, lon2, h2):
	#Calculates Range, Azimuth, Elevation in SEZ coordinate frame from SITE to UAV
	#INPUT:
	# lat1, lon1, h1 - Site Location
	# lat2, lon2, h2 - UAV location
	#OUTPUT:
	# Slant Range, Azimuth, Elevation

    lat1 = lat1 * deg2rad
    lon1 = lon1 * deg2rad
    lat2 = lat2 * deg2rad
    lon2 = lon2 * deg2rad

    r_site   = np.array(LLH_To_ECEF(lat1, lon1, h1))
    r_uav    = np.array(LLH_To_ECEF(lat2, lon2, h2))
    rho_ecef = r_uav - r_site

    ECEF_2_SEZ_ROT = np.array([[sin(lat1) * cos(lon1), sin(lat1) * sin(lon1), -1 * cos(lat1)],
                               [-1 * sin(lon1)       , cos(lon1)            , 0             ],
                               [cos(lat1) * cos(lon1), cos(lat1) * sin(lon1), sin(lat1)     ]])

    rho_sez = np.dot(ECEF_2_SEZ_ROT ,rho_ecef)
    rho_mag = np.linalg.norm(rho_sez)
    el = asin(rho_sez[2]/rho_mag) * rad2deg# * -1
    az_asin = asin(rho_sez[1]/sqrt(pow(rho_sez[0],2)+pow(rho_sez[1], 2))) * rad2deg
    az_acos = acos(-1 * rho_sez[0]/sqrt(pow(rho_sez[0],2)+pow(rho_sez[1], 2))) * rad2deg
    #print az_asin, az_acos
    #Perform Quadrant Check:
    if (az_asin >= 0) and (az_acos >= 0): az = az_acos# First or Fourth Quadrant
    else: az = 360 - az_acos# Second or Third Quadrant
    #This is the Azimuth From the TARGET to the UAV
    #Must convert to Back Azimuth:
    back_az = az + 180
    if back_az >= 360:  back_az = back_az - 360
    #print az, back_az
    # rho_mag in kilometers, range to target
    # back_az in degrees, 0 to 360
    # el in degrees, negative = down tilt, positive = up tilt
    result = {}
    result['rho_mag'] = rho_mag
    #result['az'] = back_az
    result['az'] = az
    result['el'] = el
    #return rho_mag, back_az, el
    return result

def swivel(yaw, pitch, roll, rho_mag, az, el):
    yaw = yaw * deg2rad
    pitch = pitch * deg2rad
    roll = roll * deg2rad
    az = az * deg2rad
    el = el * deg2rad
    R1 = Rot1(roll)
    R2 = Rot2(pitch)
    R3 = Rot3(yaw)
    DCM = R1*R2*R3
    #print np.linalg.inv(DCM)
    vecBody = np.matrix([[rho_mag],[az],[el]])
    vecBodyPrime = np.linalg.inv(DCM)*vecBody
    #print vecBodyPrime
    az_prime = float(vecBodyPrime[1]) * rad2deg
    el_prime = float(vecBodyPrime[2]) * rad2deg

    return az_prime, el_prime

def Rot1(theta):
    R1 = np.matrix([[1,0,0],[0, cos(theta),sin(theta)],[0,-1*sin(theta),cos(theta)]])
    return R1

def Rot2(theta):
    R2 = np.matrix([[cos(theta),0,-1*sin(theta)],[0,1,0],[sin(theta),0,cos(theta)]])
    return R2

def Rot3(theta):
    R3 = np.matrix([[cos(theta),sin(theta),0],[-1*sin(theta),cos(theta),0],[0,0,1]])
    return R3
