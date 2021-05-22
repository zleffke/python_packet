#!/usr/bin/env python3

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
from cartopy.io.img_tiles import OSM

imagery = OSM()

fig = plt.figure()
ax = fig.add_subplot(1, 1, 1, projection=imagery.crs)
ax.set_extent([-119.0, -116, 32, 34], crs=ccrs.PlateCarree())
ax.gridlines()
# #states_provinces = cfeature.NaturalEarthFeature(
#         category='cultural',
#         name='admin_1_states_provinces_lines',
#         scale='10m',
#         facecolor='none')
# ax.add_feature(states_provinces, edgecolor='gray')
# ax.add_feature(cfeature.BORDERS, linestyle=":")
#ax.add_feature(cfeature.STATES.with_scale('10m'))
land_10m = cfeature.NaturalEarthFeature('physical', 'land', '10m',
                                        edgecolor='black',
                                        facecolor='grey'
                                        #facecolor=cfeature.COLORS['land']
                                        )

coast_10m = cfeature.NaturalEarthFeature('physical', 'coastline', '10m',
                                        edgecolor='black',
                                        facecolor='white')

#ocean_10m = cfeature.NaturalEarthFeature('physical', 'ocean', '10m',
#                                         edgecolor='black',
#                                         facecolor='blue')

ax.add_feature(land_10m)
ax.add_feature(coast_10m)
#ax.add_feature(ocean_10m)

# ax = plt.axes(projection=ccrs.PlateCarree())
# ax.set_extent([-119.12, -116.2, 32.5, 33.9], crs=ccrs.PlateCarree())
#ax.add_image(imagery, 5)
#ax.coastlines('10m')
plt.show()
