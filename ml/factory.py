from .isolation_forest import IsolationForestModel
from .autoencoder import AutoencoderModel
from .one_class_svm import OneClassSVMModel
from .decision_tree_classifier import DecisionTreeURLModel
from .random_forest_classifier import RandomForestURLModel
from .svm_classifier import LinearSVMURLModel

class ModelFactory:
    """Factory to instantiate anomaly detection models by name."""
    _models = {
        'IsolationForest': IsolationForestModel,
        'Autoencoder': AutoencoderModel,
        'OneClassSVM': OneClassSVMModel,
        'DecisionTree':DecisionTreeURLModel,
        'RandomForest':RandomForestURLModel,
        'LinearSVM':LinearSVMURLModel,
    }

    @classmethod
    def create(cls, model_name: str, **kwargs):
        try:
            model_cls = cls._models[model_name]
        except KeyError:
            raise ValueError(f"Unsupported model: {model_name}") from None
        return model_cls(**kwargs)