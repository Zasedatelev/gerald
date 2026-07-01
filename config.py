import os
 
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
MINI_APP_URL = os.getenv("MINI_APP_URL", "")
 
_db_user = os.getenv("DB_USER", "olegzasedatelev")
_db_name = os.getenv("DB_NAME", "olegzasedatelev")
_db_host = "amvera-olegz2026-cnpg-testapp-bd-rw"
_default_db_url = f"postgresql://{_db_user}@{_db_host}/{_db_name}"
DATABASE_URL = os.getenv("DATABASE_URL", _default_db_url)
 
JWT_SECRET  = os.getenv("JWT_SECRET", "change_me_in_production_very_long_secret")
JWT_EXPIRES = int(os.getenv("JWT_EXPIRES_HOURS", "24"))
 
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("PORT", os.getenv("API_PORT", "8000")))
 

PASS_PERCENT = int(os.getenv("PASS_PERCENT", "100"))
