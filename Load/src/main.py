import load_news
import load_satellite
import load_stock_data
import load_coordinates
from logging_config import setup_logging

if __name__ == '__main__':
    setup_logging()

    load_news.main()
    load_satellite.main()
    load_stock_data.main()
    load_coordinates.main()
