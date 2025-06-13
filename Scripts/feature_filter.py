from datetime import datetime
import numpy as np
import operator
from functools import reduce
from typing import Dict
import pandas as pd

# These should be imported or passed in, but for now, we keep them as module-level variables for compatibility
missing_date_field = 'date Rem'
typeField = 'thoroughfa'
roadTypeExclude = np.array([])

class FeatureFilter:
    @staticmethod
    def determine_rail(sourceName):
        return 'rail' in str(sourceName).lower()

    @staticmethod
    def filter_big_features(last_year, date_field, missing, source_gdf, last_date, threshold_date, isRail):
        conditions = []
        conditions.append(source_gdf[date_field] < threshold_date)
        if last_year != "0000":
            conditions.append(source_gdf[date_field] > last_date)
        if missing:
            conditions.append(
                (source_gdf[missing_date_field].isna()) | (source_gdf[missing_date_field] >= threshold_date)
            )
        elif not isRail:
            conditions.append(~source_gdf[typeField].isin(roadTypeExclude))
        mask = reduce(operator.and_, conditions)
        filtered_gdf = source_gdf[mask].copy()
        return filtered_gdf

    @staticmethod
    def filter_features(last_year, date_field, missing, source_gdf, last_date, threshold_date, isRail=None):
        conditions = []
        conditions.append(source_gdf[date_field] < threshold_date)
# Ensure the date_field is a datetime object
        source_gdf[date_field] = pd.to_datetime(source_gdf[date_field])
        if last_year != "0000":
            conditions.append(source_gdf[date_field].dt.date > last_date)
                # New condition for 1999 and '12-01-1999'
        if int(last_year) <= 1999 and threshold_date >= datetime(1999, 12, 31).date():
            exclude_date_1999 = datetime(1999, 12, 30).date()
            conditions.append(source_gdf[date_field].dt.date != exclude_date_1999)
        if missing:
            conditions.append(
                (source_gdf[missing_date_field].isna()) | (source_gdf[missing_date_field] >= threshold_date)
            )
        
        mask = reduce(operator.and_, conditions)
        filtered_gdf = source_gdf[mask].copy()
        return filtered_gdf
