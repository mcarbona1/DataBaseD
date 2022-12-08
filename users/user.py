import hashlib
import re
import sys
sys.path.append('..')
from distributorScraper import sqlFunctions

def login(user: str, password: str) -> bool:
    user = user.lower() # usernames are case insensitive
    password = hashlib.sha256(password.encode()).hexdigest() # encrypt password
    connection = sqlFunctions.MySQL_connect("localhost", "rwachte2", "rwachte2", "pwpwpwpw")
    cursor = connection.cursor()
    cursor.execute(f"select password from USERS where username = %(user)s or email = %(user)s;",{
        'user': user
    })

    results = cursor.fetchall()
    if not results:
        return False
    
    return password == results[0][0]

# authenticate identical passwords on front end
def signup(username: str, email: str, password: str):
    if len(password) < 8 or len(password) > 64:
        raise ValueError("Invalid password. Must be between 8-64 characters long")

    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    if not re.fullmatch(regex, email):
        raise ValueError("Please use a valid email address.")

    username = username.lower() # usernames are case insensitive
    email = email.lower() # emails are case insensitive
    password = hashlib.sha256(password.encode()).hexdigest() # encrypt password
    connection = sqlFunctions.MySQL_connect("localhost", "rwachte2", "rwachte2", "pwpwpwpw")
    cursor = connection.cursor()
    cursor.execute(f"select username, email from USERS;")

    results = cursor.fetchall()
    usernames = set(result[0] for result in results)
    emails = set(result[1] for result in results)

    if username not in usernames and email not in emails:
        cursor.execute(f"INSERT INTO USERS (username, email, password) VALUES (%(username)s, %(email)s, %(password)s)", {
            'username': username, 'email': email, 'password': password
        })
        connection.commit()
        return True
    elif email in emails:
        raise ValueError("An account with that email already exists.")
    elif username in usernames:
        raise ValueError("An account with that username already exists.")

def change_password(email: str, password: str):
    password = hashlib.sha256(password.encode()).hexdigest() # encrypt password
    connection = sqlFunctions.MySQL_connect("localhost", "rwachte2", "rwachte2", "pwpwpwpw")
    cursor = connection.cursor()
    cursor.execute(f"update USERS set password = %(password)s where email = %(email)s", {
        'password': password, 'email': email
    })
    connection.commit()

def main():
    print("***Login Demo***")
    choice = input("'sign up', 'login', or 'change password': ")
    if choice == 'sign up':
        username = input("username: ")
        email = input("email: ")
        password = input("password: ")
        if password != input("enter password again: "):
            print("passwords do not match")
            return

        try:
            print(signup(username, email, password))
        except Exception as e:
            print(e)

    elif choice == 'login':
        user = input("username or email: ")
        password = input("password: ")

        try:
            print(login(user, password))
        except Exception as e:
            print(e)

    elif choice == 'change password':
        email = input("email: ")
        # send email and verify confirmation code
        password = input("password: ")

        change_password(email, password)
        print("new password created")

if __name__ == "__main__":
    main()