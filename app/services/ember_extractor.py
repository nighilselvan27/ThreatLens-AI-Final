from ember.features import PEFeatureExtractor
import numpy as np
import os
import pandas as pd
extractor = PEFeatureExtractor(feature_version=2)


def extract_ember_features(file_path: str):

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"{file_path} not found")

    with open(file_path, "rb") as f:
        bytez = f.read()

    features = extractor.feature_vector(bytez)

    features = np.array(features).reshape(1, -1)

    columns = [f"F{i}" for i in range(1, 2382)]

    return pd.DataFrame(features, columns=columns)