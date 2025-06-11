import numpy as np
import operator
from functools import reduce
from typing import Dict

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
        if last_year != "0000":
            conditions.append(source_gdf[date_field] > last_date)
        if missing:
            conditions.append(
                (source_gdf[missing_date_field].isna()) | (source_gdf[missing_date_field] >= threshold_date)
            )
        mask = reduce(operator.and_, conditions)
        filtered_gdf = source_gdf[mask].copy()
        return filtered_gdf
