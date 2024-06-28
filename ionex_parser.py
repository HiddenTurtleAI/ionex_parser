import datetime
import numpy as np
import pandas as pd
import imageio.v2 as imageio
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import os


def flatten(xss):
    return [x for xs in xss for x in xs]


def plot_map(df, map_num, output_dir, epoch, map_name):
    fig = plt.figure(figsize=(12, 8))
    ax = plt.axes(projection=ccrs.PlateCarree())

    # Add coastlines and borders
    ax.add_feature(cfeature.COASTLINE)
    ax.add_feature(cfeature.BORDERS, linestyle=':')

    # Display data as contour map
    contour = ax.contourf(df.columns, df.index, df.values, transform=ccrs.PlateCarree(), cmap='viridis')

    # Add colorbar
    cbar = plt.colorbar(contour, ax=ax, orientation='horizontal', pad=0.05)
    cbar.set_label('TEC Values')

    # Set axis limits
    ax.set_xlim(-180, 180)
    ax.set_ylim(-90, 90)

    # Title
    plt.title(f'Global TEC Map - EPOCH: {epoch} \n {map_name}')

    # Save the figure
    output_path = os.path.join(output_dir, f'map_{map_num}.png')
    plt.savefig(output_path)
    plt.close(fig)


file = 'ionex/JPL0OPSFIN_20240350000_01D_02H_GIM.INX' # path to your INX file 
# file = 'ionex/ESA0OPSFIN_20240350000_01D_02H_GIM.INX'
# file = 'ionex/COD0OPSFIN_20240350000_01D_01H_GIM.INX'
# file = 'ionex/CAS0OPSFIN_20240350000_01D_30M_GIM.INX'
output_dir = 'maps' # path to the folder you wish to store maps in 
gif_output_dir = 'gifs'# path to the folder you wish to store gifs in 
dataframe_output_dir = 'ionex/dataframes' # path to the folder you wish to store csv ionex maps in 
os.makedirs(output_dir, exist_ok=True)
os.makedirs(dataframe_output_dir, exist_ok=True)
os.makedirs(gif_output_dir, exist_ok=True)
INTERVAL = 2 # interval of tec map (2H, 1H, 30M) if 30M -> INTERVAl = 0.5
BREAK_AT = int(24/INTERVAL + 1)
result = {}
lons = np.arange(-180, 185, 5)
columns = ['fi'] + lons.tolist()
data = []
MAP_NUM = 1
EPOCHS = []
print('BREAK AT: ', BREAK_AT)
with open(file,'r') as ion:
    lines = ion.readlines()
    for num, line in enumerate(lines):
        if 'EXPONENT' in line:
            K = int(line.split()[0])
        if 'END OF HEADER' in line:
            print('END OF HEADER AT NUM: ', num)
            break
    for idx, line in enumerate(lines[num+1:]):
        if 'START OF TEC MAP' in line:
            MAP_NUM = line.split()[0]
            print('MAP NUMBER: ', MAP_NUM)
            if MAP_NUM == f'{BREAK_AT}':
                break
        if 'EPOCH OF CURRENT MAP' in line:
            spl = line.split()
            spl[:6] = [int(i) for i in spl[:6]]
            MAP_EPOCH = datetime.datetime(year=spl[0], month=spl[1], day=spl[2], hour=spl[3], minute=spl[4], second=spl[5])
            EPOCHS.append(MAP_EPOCH)
        if 'LAT/LON1/LON2/DLON/H' in line:
            latline = line.split()[0].replace('-',' -')
            if len(latline.split(' ')) == 3:
                lat = latline.split(' ')[1]
            elif len(latline.split(' ')) == 2:
                lat = latline.split(' ')[0]
            d = [l.split() for l in lines[num+idx+2:num+idx+7]]
            data_for_lat = [int(i)*10**K for i in flatten(d)]
            row = np.array([float(lat)] + data_for_lat)
            data.append(row)
        if len(data)==71:
            d = pd.DataFrame(data, columns=columns)
            d.set_index(['fi'],inplace=True)
            result[MAP_NUM] = d
            data = []

full = pd.concat(result,keys=result.keys(),names=['MAP_NUM','fi'])

map_name = file.split('/')[1]
AGENCY = map_name[:3]
for num, epoch in zip(range(1,BREAK_AT), EPOCHS):
    print(num)
    df = full.loc[f'{num}']
    plot_map(df, num, output_dir,epoch,map_name)
images = []
for map_num in full.index.get_level_values(0).unique():
    filename = os.path.join(output_dir, f'map_{map_num}.png')
    print(filename)
    images.append(imageio.imread(filename))

gif_path = f'{gif_output_dir}/{AGENCY}_global_tec_maps.gif'
imageio.mimsave(gif_path, images, duration=0.5)  # Adjust duration as needed
full.to_csv(f'{dataframe_output_dir}/{AGENCY}_MAP.csv')
print(f"Animation saved to {gif_path}")
