"""_jobs file for 'addrapn' layer sde extraction."""
from poseidon.util import general
from poseidon.util import geospatial
import pandas as pd
from collections import OrderedDict
import logging

conf = general.config
table = 'ADDRAPN'
prod_dir = conf['prod_data_dir']
layername = 'addrapn_datasd'
layer = prod_dir + '/' + layername

dtypes = OrderedDict([
        ('objectid', 'int:9'),
        ('addrnmbr', 'int:6'),
        ('addrfrac', 'str:5'),
        ('addrpdir', 'str:3'),
        ('addrname', 'str:30'),
        ('addrpostd', 'str:5'),
        ('addrsfx', 'str:6'),
        ('addrunit', 'str:6'),
        ('addrzip', 'int:6'),
        ('add_type', 'str:6'),
        ('roadsegid', 'int:9'),
        ('apn', 'int:12'),
        ('asource', 'str:6'),
        ('plcmt_loc', 'str:6'),
        ('community', 'str:20'),
        ('parcelid', 'int:10'),
        ('usng', 'str:20')
    ])

gtype = 'Point'


def sde_to_shp():
    """SDE table to Shapefile."""
    logging.info('Extracting {layername} layer from SDE.'.format(
        layername=layername))
    df = geospatial.extract_sde_data(table=table,
                                     where="ADDRJUR = 'SD'")

    logging.info('Processing {layername} df.'.format(layername=layername))
    df = df.rename(columns={'placement_location': 'plcmt_loc',
                            'address_type': 'add_type'})
    df = df.fillna('')

    logging.info('Converting {layername} df to shapefile.'.format(
        layername=layername))
    geospatial.df2shp(df=df,
                      folder=prod_dir,
                      layername=layername,
                      dtypes=dtypes,
                      gtype=gtype,
                      epsg=2230)
    return 'Successfully converted {layername} to shapefile.'.format(
           layername=layername)
