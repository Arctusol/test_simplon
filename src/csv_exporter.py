import os
import csv
from datetime import datetime
import logging
import pytz

logger = logging.getLogger(__name__)

class CSVExporter:
    def __init__(self, base_dir="/app/historical_data"):
        self.base_dir = base_dir
        self.subdirs = {
            'revenue': 'revenue_history',
            'stores': 'store_history',
            'products': 'product_history',
            'stock': 'stock_history'
        }
        self.create_export_directories()

    def create_export_directories(self):
        """Create the directory structure for historical data"""
        try:
            # Create base directory
            os.makedirs(self.base_dir, exist_ok=True)
            
            # Create subdirectories
            for subdir in self.subdirs.values():
                os.makedirs(os.path.join(self.base_dir, subdir), exist_ok=True)
            
            logger.info("Export directories created successfully")
        except Exception as e:
            logger.error(f"Error creating export directories: {str(e)}")
            raise

    def get_timestamp(self):
        """Get current timestamp in Paris timezone"""
        paris_tz = pytz.timezone('Europe/Paris')
        current_time = datetime.now(paris_tz)
        return current_time.strftime('%Y-%m-%d_%H-%M')

    def generate_filename(self, data_type):
        """Generate filename with timestamp for a given data type"""
        timestamp = self.get_timestamp()
        return os.path.join(self.base_dir, 
                          self.subdirs[data_type], 
                          f"{timestamp}_{data_type}.csv")

    def export_revenue_data(self, total_revenue, total_employees):
        """Export revenue data to CSV"""
        try:
            filename = self.generate_filename('revenue')
            timestamp = self.get_timestamp()
            
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'total_revenue', 'total_employees'])
                writer.writerow([timestamp, f"{total_revenue:.2f}", total_employees])
            
            logger.info(f"Revenue data exported to {filename}")
            return filename
        except Exception as e:
            logger.error(f"Error exporting revenue data: {str(e)}")
            raise

    def export_store_data(self, store_data):
        """Export store performance data to CSV"""
        try:
            filename = self.generate_filename('stores')
            timestamp = self.get_timestamp()
            
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'store_id', 'city', 'revenue', 'employee_count'])
                for store in store_data:
                    writer.writerow([
                        timestamp,
                        store['id'],
                        store['city'],
                        f"{store['revenue']:.2f}",
                        store['employees']
                    ])
            
            logger.info(f"Store data exported to {filename}")
            return filename
        except Exception as e:
            logger.error(f"Error exporting store data: {str(e)}")
            raise

    def export_product_data(self, product_data):
        """Export product sales data to CSV"""
        try:
            filename = self.generate_filename('products')
            timestamp = self.get_timestamp()
            
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'product_name', 'units_sold', 'revenue'])
                for product in product_data:
                    writer.writerow([
                        timestamp,
                        product['name'],
                        product['units'],
                        f"{product['revenue']:.2f}"
                    ])
            
            logger.info(f"Product data exported to {filename}")
            return filename
        except Exception as e:
            logger.error(f"Error exporting product data: {str(e)}")
            raise

    def export_stock_data(self, total_units, total_value):
        """Export stock information to CSV"""
        try:
            filename = self.generate_filename('stock')
            timestamp = self.get_timestamp()
            
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'total_units', 'total_value'])
                writer.writerow([timestamp, total_units, f"{total_value:.2f}"])
            
            logger.info(f"Stock data exported to {filename}")
            return filename
        except Exception as e:
            logger.error(f"Error exporting stock data: {str(e)}")
            raise

    def export_all_data(self, analysis_results):
        """Export all analysis data to respective CSV files"""
        try:
            # Export revenue data
            self.export_revenue_data(
                analysis_results['total_revenue'],
                analysis_results['total_employees']
            )

            # Export store data
            store_data = [
                {
                    'id': store[0],
                    'city': store[1],
                    'revenue': store[2],
                    'employees': store[3]
                }
                for store in analysis_results['store_data']
            ]
            self.export_store_data(store_data)

            # Export product data
            product_data = [
                {
                    'name': product[0],
                    'units': product[1],
                    'revenue': product[2]
                }
                for product in analysis_results['product_data']
            ]
            self.export_product_data(product_data)

            # Export stock data
            self.export_stock_data(
                analysis_results['total_stock'],
                analysis_results['stock_value']
            )

            logger.info("All data exported successfully")
        except Exception as e:
            logger.error(f"Error during data export: {str(e)}")
            raise