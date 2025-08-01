from flask import Blueprint, render_template, request, redirect, flash, url_for, current_app
from ids.ml.factory import ModelFactory
from ids.core import config
import pandas as pd
from pathlib import Path
import os
import re
from datetime import datetime

bp = Blueprint('train', __name__, url_prefix='/train')

def extract_timestamp(filename):
    match = re.search(r'_(\d{8}T\d{6})', filename)
    if match:
        return datetime.strptime(match.group(1), "%Y%m%dT%H%M%S")
    return datetime.min

@bp.route('/', methods=['GET', 'POST'])
def train_model():
    training_dir = Path(current_app.root_path) / 'static' / 'training_results'
    training_dir.mkdir(parents=True, exist_ok=True)

    # Get and sort images by timestamp
    image_files = [
        f for f in os.listdir(training_dir) if f.endswith('.png')
    ]
    image_files.sort(key=lambda f: extract_timestamp(f), reverse=True)

    # Trim to latest 6
    recent_images = image_files[:6]

    # Remove old images beyond the latest 6
    for old_image in image_files[6:]:
        try:
            os.remove(training_dir / old_image)
        except Exception as e:
            print(f"Error removing {old_image}: {e}")

    if request.method == 'POST':
        model_name = request.form['model_type']
        model = ModelFactory.create(model_name)
        df = pd.read_csv(config.BASE_DIR / 'data' / 'normal_traffic_baseline.csv')
        data = df.select_dtypes(include='number').values
        plot_path = model.train_and_plot(data, save_dir=training_dir)
        flash(f"{model_name} trained successfully.")
        recent_images.insert(0, plot_path.name)
        recent_images = recent_images[:6]
        return render_template('train_model.html', training_image=plot_path.name, recent_images=recent_images)

    return render_template('train_model.html', recent_images=recent_images)
