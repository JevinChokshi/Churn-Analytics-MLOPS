from sklearn.base import BaseEstimator, TransformerMixin
import numpy as np
import pandas as pd

class TechnicalFrustrationIndex(BaseEstimator, TransformerMixin):
    def __init__(self, feature_weights: dict):
        self.feature_weights = feature_weights
        self.means_ = {}
        self.stds_ = {}

    def fit(self, X: pd.DataFrame, y=None):
        for feature in self.feature_weights.keys():
            self.means_[feature] = X[feature].mean()
            self.stds_[feature] = X[feature].std() + 1e-9
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        X_transformed = X.copy()
        tfi_array = np.zeros(len(X))

        for feature, weight in self.feature_weights.items():
            z_score = (X[feature] - self.means_[feature]) / self.stds_[feature]
            tfi_array += weight * z_score

        X_transformed["technical_frustration_index"] = tfi_array
        return X_transformed