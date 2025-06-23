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
    def filter_features( date_field, source_gdf):
        conditions = []
# Ensure the date_field is a datetime object
        source_gdf[date_field] = pd.to_datetime(source_gdf[date_field])
                # condition for 1999 and '12-01-1999' to reject unmapped features
        exclude_date_1999 = datetime(1999, 12, 30).date()
        conditions.append(source_gdf[date_field].dt.date != exclude_date_1999)
        mask = reduce(operator.and_, conditions)
        filtered_gdf = source_gdf[mask].copy()
        return filtered_gdf
