import random
from locust import HttpUser, task, between


# These are pre-created test wallets
# We'll populate these after running setup
SENDER_WALLET_ID = "7fbdfa4c-4f48-4d23-bf93-7a7c3df25c24"
RECEIVER_WALLET_ID = "0c2221ab-6f4a-47ea-9462-ffabd7128c18"

# JWT token for test user
TOKEN = ""  # We'll fill this in


class LedgerUser(HttpUser):
    """
    Simulates a user hitting our API endpoints.
    wait_time: wait 0.1-0.5 seconds between requests
    """
    wait_time = between(0.1, 0.5)
    token = None

    def on_start(self):
        """Called when a user starts — login and get token."""
        response = self.client.post(
            "/auth/token",
            json={
                "email": "test@example.com",
                "password": "test123"
            }
        )
        if response.status_code == 200:
            self.token = response.json()["access_token"]

    def get_headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    @task(10)
    def check_balance(self):
        """
        Weight 10 — most common operation.
        This hits Redis cache — should be sub-10ms.
        """
        self.client.get(
            f"/wallet/{SENDER_WALLET_ID}/balance",
            headers=self.get_headers(),
            name="/wallet/balance"
        )

    @task(3)
    def get_ledger(self):
        """Weight 3 — less frequent."""
        self.client.get(
            f"/ledger/{SENDER_WALLET_ID}",
            headers=self.get_headers(),
            name="/ledger"
        )

    @task(1)
    def health_check(self):
        """Weight 1 — least frequent."""
        self.client.get("/health")