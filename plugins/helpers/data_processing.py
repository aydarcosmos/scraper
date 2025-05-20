import os
import xml.etree.ElementTree as ET
from datetime import datetime

def download_files(**context):
    """Download XML files from URLs and save them locally"""
    import requests
    
    urls = [
        "https://forecast.weather.gov/xml/current_obs/KJFK.xml",
        "https://www.floatrates.com/daily/usd.xml"
    ]
    download_dir = "downloads"
    
    # Create directory for downloads if it doesn't exist
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)
    
    for url in urls:
        try:
            print(f"Downloading {url}...")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Extract filename from URL
            filename = os.path.join(download_dir, url.split('/')[-1])
            with open(filename, 'wb') as f:
                f.write(response.content)
            
            print(f"Successfully downloaded: {url} to {filename}")
            print(f"File size: {os.path.getsize(filename) / 1024:.2f} KB")
        except Exception as e:
            print(f"Error downloading {url}: {str(e)}")
            raise

def parse_files(**context):
    """Parse downloaded XML files and extract required data"""
    download_dir = "downloads"
    weather_data = None
    currency_data = None
    
    # Parse weather XML
    try:
        weather_file = os.path.join(download_dir, "KJFK.xml")
        if not os.path.exists(weather_file):
            print(f"Weather file not found: {weather_file}")
        else:
            tree = ET.parse(weather_file)
            root = tree.getroot()
            
            # Convert temperature from F to C
            temp_f = float(root.find('.//temperature_string').text.split()[0])
            temp_c = (temp_f - 32) * 5/9
            weather_data = {
                'temperature_c': round(temp_c, 1),
                'timestamp': datetime.now().isoformat()
            }
            print(f"Successfully parsed weather data: {weather_data}")
    except Exception as e:
        print(f"Error parsing weather XML: {str(e)}")
    
    # Parse currency XML
    try:
        currency_file = os.path.join(download_dir, "usd.xml")
        print(f"Parsing currency file: {currency_file}")
        
        # Check if file exists and is not empty
        if not os.path.exists(currency_file):
            print(f"Currency file not found: {currency_file}")
        else:
            # Parse the XML
            tree = ET.parse(currency_file)
            root = tree.getroot()
            
            # Find all item elements
            items = root.findall('.//item')
            print(f"Found {len(items)} currency items in the XML")
            
            # Look for Chinese Yuan (CNY)
            for item in items:
                # Get target currency code (e.g., 'CNY')
                target_currency = item.find('targetCurrency')
                if target_currency is None:
                    continue
                    
                target_code = target_currency.text
                
                # Get exchange rate
                exchange_rate = item.find('exchangeRate')
                if exchange_rate is None:
                    continue
                    
                # Get currency name
                currency_name = item.find('targetName')
                name = currency_name.text if currency_name is not None else "Unknown"
                
                print(f"Found currency - Code: {target_code}, Name: {name}")
                
                # Check if this is Chinese Yuan (CNY)
                if target_code == 'CNY':
                    try:
                        rate = float(exchange_rate.text)
                        print(f"Found CNY rate: {rate}")
                        currency_data = {
                            'usd_to_cny': round(rate, 4),
                            'timestamp': datetime.now().isoformat()
                        }
                        break
                    except (ValueError, TypeError) as e:
                        print(f"Error parsing rate '{exchange_rate.text}': {str(e)}")
            else:
                print("CNY currency not found in the XML file")
                print("Available currency codes:")
                for item in items[:10]:  # Show first 10 for brevity
                    code = item.find('targetCurrency')
                    name = item.find('targetName')
                    rate = item.find('exchangeRate')
                    if code is not None and name is not None and rate is not None:
                        print(f"- {code.text}: {name.text} (Rate: {rate.text}")
    except Exception as e:
        print(f"Error parsing currency XML: {str(e)}")
    
    result = {'weather': weather_data, 'currency': currency_data}
    print(f"Returning parsed data: {result}")
    return result

def save_to_db(**context):
    """Save parsed data to PostgreSQL database"""
    # Get data from XCom
    task_instance = context['task_instance']
    parsed_data = task_instance.xcom_pull(task_ids='parse_files')
    
    if not parsed_data:
        print("No data to save")
        return
    
    print(f"Saving data to database: {parsed_data}")
    
    # Get database connection
    from airflow.providers.postgres.hooks.postgres import PostgresHook
    
    try:
        # Connect to the database
        pg_hook = PostgresHook(postgres_conn_id='postgres_default')
        conn = pg_hook.get_conn()
        cursor = conn.cursor()
        
        # Save weather data if available
        if 'weather' in parsed_data and parsed_data['weather']:
            weather = parsed_data['weather']
            print(f"Saving weather data: {weather}")
            cursor.execute("""
                INSERT INTO weather_data (temperature_c, timestamp)
                VALUES (%s, %s)
            """, (
                weather.get('temperature_c'),
                weather.get('timestamp')
            ))
            print(f"Successfully saved weather data")
        else:
            print("No weather data to save")
        
        # Save currency data if available
        if 'currency' in parsed_data and parsed_data['currency']:
            currency = parsed_data['currency']
            print(f"Saving currency data: {currency}")
            cursor.execute("""
                INSERT INTO currency_data (usd_to_cny, timestamp)
                VALUES (%s, %s)
            """, (
                currency.get('usd_to_cny'),
                currency.get('timestamp')
            ))
            print(f"Successfully saved currency data")
        else:
            print("No currency data to save")
        
        # Commit the transaction
        conn.commit()
        print("Successfully committed transaction")
        
    except Exception as e:
        print(f"Error saving to database: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
            print("Transaction rolled back due to error")
        raise
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
            print("Database connection closed")
        print("No currency data to save")
