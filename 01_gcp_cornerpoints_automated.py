import os
del os.environ['PROJ_LIB']
from osgeo import gdal, osr
import pandas as pd
import requests
from PIL import Image

input_csv = r"D:\Onedrive\OneDrive - University of Cambridge\General - ARCH_MAHSA\MAHSA_Mapping\Project Cast Away\AreaOfInterest_PreviewImages_data2.csv"
source_df = pd.read_csv(input_csv, encoding = "ISO-8859-1")
source_df.columns = source_df.columns.str.replace(' ', '_')
source_df['url'] = "https://ims.cr.usgs.gov/browse/declass3/" + source_df['Mission'] + "/" + source_df['Operations_Number'].map(lambda x: f'{x:0>5}') + "/" + source_df['Camera'] + "/" + source_df['Entity_ID'] + ".jpg"
source_df['url'] = source_df['url'].astype('|S') # which will by default set the length to the max len it encounters

output_path = "D:\Onedrive\OneDrive - University of Cambridge\General - ARCH_MAHSA\MAHSA_Mapping\Project Cast Away\CAST Imagery\Declass3\Preview Images USGS"

#gdal
kwargs = {
    'format': 'GTiff'
}

image_urls = source_df[['NW_Corner_Lat_dec', 'NW_Corner_Long_dec', 'NE_Corner_Lat_dec', 'NE_Corner_Long_dec', 'SE_Corner_Lat_dec', 'SE_Corner_Long_dec', 'SW_Corner_Lat_dec', 'SW_Corner_Long_dec', 'url', 'Mission', 'Region']]
# print(image_urls)
# loop through urls in source excel file of different preview images
for row in image_urls.itertuples():
    try:
        # get file urls
        img_blob = requests.get(row.url, timeout=5).content
        with open(str(row.url).split('/')[-1].replace("'",""), 'wb') as img_file:
            # print image file from url
            name = row.Region + '_' + row.Mission + '_' + str(row.url).split('/')[-1].replace(".jpg'", "")
            print(name)
            #export image as jpg to folder
            image = img_file.write(img_blob)
            #get path to exported image
            img_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),img_file.name)
            # convert image to .tif and create folder if not exist
            try:
                os.makedirs(output_path + "/output_tif/")
            except OSError:
                pass
            gdal.Translate(output_path + "/output_tif/" + name + ".tif", img_path, **kwargs)
            #get path to exported tif image
            img_tif = (output_path + "/output_tif/" + name + ".tif")
            #open image in gdal for referencing
            ds = gdal.Open(img_tif, gdal.GA_Update)
            # # Set spatial reference:
            sr = osr.SpatialReference()
            sr.ImportFromEPSG(4326)  # 4326 refers to the WGS84, but can use any desired projection
            # Calculate image pixel size for corner points
            width, height = Image.open(img_tif).size
            print(width, height)
            # Enter the GCPs
            #   Format: [map x-coordinate(longitude)], [map y-coordinate (latitude)], [elevation],
            #   [image column index(x)], [image row index (y)]
            gcps = [
                # NW corner
                gdal.GCP(row.NW_Corner_Long_dec, row.NW_Corner_Lat_dec, 0, 0, 0),
                # NE corner
                gdal.GCP(row.NE_Corner_Long_dec, row.NE_Corner_Lat_dec, 0, width, 0),
                # SE corner
                gdal.GCP(row.SE_Corner_Long_dec, row.SE_Corner_Lat_dec, 0, width, height),
                # SW corner
                gdal.GCP(row.SW_Corner_Long_dec, row.SW_Corner_Lat_dec, 0, 0, height)]
            # # Apply the GCPs to the open output file:
            ds.SetGCPs(gcps, sr.ExportToWkt())
            # # Close the output file in order to be able to work with it in other programs:
            ds = None
    except Exception as ex:
       print('Failed to get:',row.url, ex)