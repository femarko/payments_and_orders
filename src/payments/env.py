from payments.paths import BASE_DIR


 
def init_env(use_load_dotenv: bool, env_file: str = ".env"):
    if use_load_dotenv:
        from dotenv import load_dotenv
        load_dotenv(
            dotenv_path=BASE_DIR / env_file
        )
