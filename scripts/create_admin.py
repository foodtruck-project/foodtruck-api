import argparse
import httpx
import sys

def create_admin_user(username, full_name, email, password, api_url="http://foodtruck.docker.localhost"):
    """
    Calls the setup API to create the first administrator user.
    """
    url = f"{api_url}/api/v1/setup/"
    payload = {
        "username": username,
        "full_name": full_name,
        "email": email,
        "password": password,
        "role": "admin",
    }

    print(f"Attempting to create admin user '{username}' at {url}...")

    try:
        with httpx.Client() as client:
            response = client.post(url, json=payload)

        if response.status_code == 201:
            print("\033[92m" + "✅ Administrator user created successfully!" + "\033[0m")
            print(response.json())
        elif response.status_code == 403:
            print("\033[93m" + "⚠️ Setup already complete. First user already exists." + "\033[0m")
        elif response.status_code == 409:
            error_detail = response.json().get('detail', 'User/email already exists.')
            print("\033[91m" + f"❌ Conflict: {error_detail}" + "\033[0m")
        else:
            response.raise_for_status()

    except httpx.RequestError as e:
        print("\033[91m" + f"❌ An error occurred while requesting {e.request.url!r}." + "\033[0m")
        print(e)
        sys.exit(1)
    except Exception as e:
        print("\033[91m" + f"❌ An unexpected error occurred: {e}" + "\033[0m")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create the first administrator user for the Food Truck API.")
    parser.add_argument("--username", required=True, help="Username for the admin user.")
    parser.add_argument("--full-name", required=True, help="Full name of the admin user.")
    parser.add_argument("--email", required=True, help="Email of the admin user.")
    parser.add_argument("--password", required=True, help="Password for the admin user.")
    parser.add_argument("--api-url", default="http://127.0.0.1:8000", help="Base URL of the API.")

    args = parser.parse_args()

    create_admin_user(
        username=args.username,
        full_name=args.full_name,
        email=args.email,
        password=args.password,
        api_url=args.api_url,
    )
