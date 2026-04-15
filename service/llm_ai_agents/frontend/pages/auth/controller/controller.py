class AuthController:
    def __init__(self, api_base_url=None):
        self.api_base_url = api_base_url
    def login(self, username, password):
        return {"success": True, "user": {"username": username}}
