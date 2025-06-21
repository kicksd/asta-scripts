from kiteconnect import KiteConnect

# 1) Initialize
kite = KiteConnect(api_key="wye4akybc8q7bf6j")

# 2) Get login URL & authorize manually
print(kite.login_url())

# 3) After login you receive a `request_token` in callback URL
# Exchange it for access token:
data = kite.generate_session("UgqcB0N3gh1OvpknlIyZywbu41Q7HzWS", api_secret="yayjdjidkw87mpzu8j7el41nq33zj7aa")
kite.set_access_token(data["access_token"])
