import logging
import os


def setup_logging():
    log_folder = os.path.join(os.path.dirname(__file__), 'logs')
    os.makedirs(log_folder, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(os.path.join(os.path.dirname(__file__), 'logs', 'app.log'))
        ]
    )
