import os
from dotenv import load_dotenv
from pathlib import Path
from urllib.parse import quote_plus

# 프로젝트 디렉토리 기준 .env 파일 로드
basedir = Path(__file__).resolve().parent.parent.parent
dotenv_path = basedir / '.env'
print(f"Loading .env file from: {dotenv_path}")
load_dotenv(dotenv_path)

def get_env_variable(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"환경 변수 '{name}'가 설정되지 않았습니다.")
    return value

class Config:
    """기본 설정"""
    ENV = os.getenv('FASTAPI_ENV', 'production')
    print(f"ENV: {ENV}")
    DEBUG = os.getenv('FASTAPI_DEBUG', 'False').lower() in ['true', '1', 't']
    TESTING = os.getenv('FASTAPI_TESTING', 'False').lower() in ['true', '1', 't']
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key')

    # 모델 설정 (로컬 LLM 사용 여부에 따라 모델 선택)
    USE_LOCAL_LLM = os.getenv('USE_LOCAL_LLM', 'False').lower() in ['true', '1', 't']
    if USE_LOCAL_LLM:
        OPENAI_MODEL_NM = 'local-llm-model'
    else:
        OPENAI_MODEL_NM = os.getenv('OPENAI_MODEL_NM', 'gpt-4o-mini')
    OPENAI_MODEL_4O = os.getenv('OPENAI_MODEL_4O', 'gpt-4o')

    # 데이터베이스 기본 설정
    DATABASE_URL = "sqlite:///:memory:"  # 기본값 설정
    ASYNC_DATABASE_URL = "sqlite+aiosqlite:///:memory:"  # 기본값 설정

    # OpenAI API 설정
    OPENAI_API_KEY = get_env_variable('OPENAI_API_KEY')

    # CORS 설정
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*')

    # 외부 API 설정
    FETCH_COUNT_LIMIT = int(os.getenv("FETCH_COUNT_LIMIT", 10))

    # 기타 설정
    SOME_OTHER_CONFIG = os.getenv('SOME_OTHER_CONFIG', 'default_value')

class DevelopmentConfig(Config):
    """개발 환경 설정"""
    DEBUG = True
    ASYNC_DATABASE_URL = f"mysql+aiomysql://{get_env_variable('DEV_DB_USERNAME')}:{quote_plus(get_env_variable('DEV_DB_PASSWORD'))}@{get_env_variable('DEV_DB_HOST')}:{get_env_variable('DEV_DB_PORT')}/{get_env_variable('DEV_DB_DATABASE')}"
    DATABASE_URL = f"mysql+pymysql://{get_env_variable('DEV_DB_USERNAME')}:{quote_plus(get_env_variable('DEV_DB_PASSWORD'))}@{get_env_variable('DEV_DB_HOST')}:{get_env_variable('DEV_DB_PORT')}/{get_env_variable('DEV_DB_DATABASE')}"
    print(f"DevelopmentConfig DATABASE_URL: {DATABASE_URL}")

class TestingConfig(Config):
    """테스트 환경 설정"""
    TESTING = True
    ASYNC_DATABASE_URL = f"mysql+aiomysql://{get_env_variable('TEST_DB_USERNAME')}:{quote_plus(get_env_variable('TEST_DB_PASSWORD'))}@{get_env_variable('TEST_DB_HOST')}:{get_env_variable('TEST_DB_PORT')}/{get_env_variable('TEST_DB_DATABASE')}"
    DATABASE_URL = f"mysql+pymysql://{get_env_variable('TEST_DB_USERNAME')}:{quote_plus(get_env_variable('TEST_DB_PASSWORD'))}@{get_env_variable('TEST_DB_HOST')}:{get_env_variable('TEST_DB_PORT')}/{get_env_variable('TEST_DB_DATABASE')}"
    print(f"TestingConfig DATABASE_URL: {DATABASE_URL}")

class ProductionConfig(Config):
    """운영 환경 설정"""
    DEBUG = False
    ASYNC_DATABASE_URL = f"mysql+aiomysql://{get_env_variable('PROD_DB_USERNAME')}:{quote_plus(get_env_variable('PROD_DB_PASSWORD'))}@{get_env_variable('PROD_DB_HOST')}:{get_env_variable('PROD_DB_PORT')}/{get_env_variable('PROD_DB_DATABASE')}"
    DATABASE_URL = f"mysql+pymysql://{get_env_variable('PROD_DB_USERNAME')}:{quote_plus(get_env_variable('PROD_DB_PASSWORD'))}@{get_env_variable('PROD_DB_HOST')}:{get_env_variable('PROD_DB_PORT')}/{get_env_variable('PROD_DB_DATABASE')}"
    print(f"ProductionConfig DATABASE_URL: {DATABASE_URL}")

# 환경 변수에 따라 적절한 설정 클래스를 반환
def get_config(env: str):
    if env == 'dev':
        return DevelopmentConfig()
    elif env == 'test':
        return TestingConfig()
    elif env == 'prod':
        return ProductionConfig()
    return Config()

current_env = os.getenv('FASTAPI_ENV', 'dev')
print(f"Current FASTAPI_ENV: {current_env}")
current_config = get_config(current_env)
print(f"Current Config DATABASE_URL: {current_config.DATABASE_URL}")
print(f"Current Config ASYNC_DATABASE_URL: {current_config.ASYNC_DATABASE_URL}")
print(f"Current Config Model Name: {current_config.OPENAI_MODEL_NM}")
