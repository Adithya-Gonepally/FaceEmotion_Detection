import pandas as pd
import os

USER_DB_PATH = os.path.join("auth", "users.csv")

def load_users():
    if not os.path.exists(USER_DB_PATH):
        return pd.DataFrame(columns=["username", "password", "role", "approved"])
    return pd.read_csv(USER_DB_PATH)

def save_users(df):
    df.to_csv(USER_DB_PATH, index=False)

def register_user(username, password):
    users_file = "auth/users.csv"

    # Create file if not exists
    if not os.path.exists(users_file):
        df = pd.DataFrame(columns=["username", "password", "role", "approved"])
        df.to_csv(users_file, index=False)

    # Load users
    df = pd.read_csv(users_file)

    # Check if username already exists
    if username in df["username"].values:
        return False, "Username already exists."

    # Add user
    new_user = {"username": username, "password": password, "role": "user", "approved": False}
    df = pd.concat([df, pd.DataFrame([new_user])], ignore_index=True)
    df.to_csv(users_file, index=False)

    return True, "Registration successful. Awaiting admin approval."


def authenticate(username, password):
    df = load_users()
    user = df[df["username"] == username]
    if not user.empty and user.iloc[0]["password"] == password:
        return True, user.iloc[0].to_dict()
    return False, None

def get_users(include_all=False):
    df = load_users()
    if include_all:
        return df
    return df[(df["role"] == "user") & (df["approved"] == False)]


def approve_user(username):
    df = load_users()
    df.loc[df["username"] == username, "approved"] = True
    save_users(df)

def remove_user(username):
    df = load_users()
    df = df[df["username"] != username]
    save_users(df)
