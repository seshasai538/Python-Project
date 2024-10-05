import csv
import re
import bcrypt
import requests
from getpass import getpass
import os

# Constants
CSV_FILE = 'regno.csv'
API_KEY = '22850de591a9c4a5b40bb36eb7ab1105'
MAX_LOGIN_ATTEMPTS = 5

def validate_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

def validate_password(password):
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'\d', password):
        return False
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False
    return True

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())

def verify_password(stored_password, provided_password):
    return bcrypt.checkpw(provided_password.encode(), stored_password)

def load_users():
    users = {}
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if 'email' in row and 'password' in row and 'security_question' in row:
                    users[row['email']] = {
                        'password': row['password'].encode(),
                        'security_question': row['security_question']
                    }
    return users

def save_users(users):
    with open(CSV_FILE, 'w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=['email', 'password', 'security_question'])
        writer.writeheader()
        for email, data in users.items():
            writer.writerow({
                'email': email,
                'password': data['password'].decode() if isinstance(data['password'], bytes) else data['password'],
                'security_question': data['security_question']
            })

def create_account():
    users = load_users()
    try:
        for _ in range(3):  # Limit attempts to 3
            email = input("Enter your email: ")
            if not validate_email(email):
                print("Invalid email format. Please try again.")
                continue
            if email in users:
                print("Email already exists. Please use a different email.")
                continue
            break
        else:
            print("Too many invalid attempts. Returning to main menu.")
            return

        for _ in range(3):  # Limit attempts to 3
            password = getpass("Enter your password: ")
            if not validate_password(password):
                print("Invalid password. It must be at least 8 characters long and contain uppercase, lowercase, digit, and special character.")
                continue
            break
        else:
            print("Too many invalid attempts. Returning to main menu.")
            return

        security_question = input("Enter a security question: ")
        security_answer = input("Enter the answer to your security question: ")

        users[email] = {
            'password': hash_password(password),
            'security_question': f"{security_question}:{security_answer}"
        }
        save_users(users)
        print("Account created successfully!")
    except Exception as e:
        print(f"An error occurred: {e}")
        print("Account creation failed. Please try again later.")

def login():
    users = load_users()
    attempts = 0
    while attempts < MAX_LOGIN_ATTEMPTS:
        email = input("Enter your email: ")
        password = getpass("Enter your password: ")

        if email in users and verify_password(users[email]['password'], password):
            print("Login successful!")
            return email
        else:
            attempts += 1
            print(f"Invalid credentials. {MAX_LOGIN_ATTEMPTS - attempts} attempts remaining.")

    print("Maximum login attempts exceeded. Exiting...")
    exit()

def forgot_password():
    users = load_users()
    email = input("Enter your registered email: ")
    if email in users:
        answer = input(f"Security question: {users[email]['security_question'].split(':')[0]}\nYour answer: ")
        if answer.lower() == users[email]['security_question'].split(':')[1].strip().lower():
            while True:
                new_password = getpass("Enter new password: ")
                if validate_password(new_password):
                    users[email]['password'] = hash_password(new_password)
                    save_users(users)
                    print("Password reset successful!")
                    break
                else:
                    print("Invalid password. Please try again.")
        else:
            print("Incorrect answer to security question.")
    else:
        print("Email not found.")

def get_air_quality(city):
    base_url = "http://api.openweathermap.org/data/2.5/air_pollution"

    # First, get the coordinates for the city
    geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={API_KEY}"
    response = requests.get(geo_url)
    if response.status_code == 200:
        data = response.json()
        if data:
            lat, lon = data[0]['lat'], data[0]['lon']

            # Now get the air quality data
            aqi_url = f"{base_url}?lat={lat}&lon={lon}&appid={API_KEY}"
            response = requests.get(aqi_url)
            if response.status_code == 200:
                aqi_data = response.json()
                return aqi_data['list'][0]['main']['aqi'], aqi_data['list'][0]['components']

    return None, None

def display_air_quality(city, aqi, components):
    print(f"\nAir Quality Information for {city}:")
    print(f"AQI: {aqi}")
    print("\nMain Pollutants:")
    for pollutant, value in components.items():
        print(f"{pollutant}: {value}")

    print("\nHealth Recommendations:")
    if aqi == 1:
        print("Air quality is good. Enjoy outdoor activities!")
    elif aqi == 2:
        print("Air quality is fair. Sensitive individuals should limit prolonged outdoor exertion.")
    elif aqi == 3:
        print("Air quality is moderate. People with respiratory or heart conditions should reduce outdoor exertion.")
    elif aqi == 4:
        print("Air quality is poor. Avoid prolonged outdoor activities. Wear a mask if necessary.")
    elif aqi == 5:
        print("Air quality is very poor. Stay indoors and keep windows closed. Wear a mask if you must go outside.")

def main():
    print("Welcome to the Air Quality Monitoring System")
    while True:
        choice = input("1. Login\n2. Create Account\n3. Forgot Password\n4. Exit\nChoose an option: ")
        if choice == '1':
            email = login()
            while True:
                city = input("Enter a city name to check air quality (or 'q' to quit): ")
                if city.lower() == 'q':
                    break
                aqi, components = get_air_quality(city)
                if aqi is not None:
                    display_air_quality(city, aqi, components)
                else:
                    print("Failed to retrieve air quality data. Please try again.")
        elif choice == '2':
            create_account()
        elif choice == '3':
            forgot_password()
        elif choice == '4':
            print("Thank you for using the Air Quality Monitoring System. Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()