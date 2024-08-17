from openai_client import ChatOpenAI
from sql_memory import SQLChatMemory, HumanMessage, AIMessage
from prompt_template import ChatPromptTemplate
from app.core.config import current_config  # 환경 설정을 가져옵니다.

# SQLChatMemory 인스턴스 생성
chat_memory = SQLChatMemory(db_url=current_config.DATABASE_URL)

# 모델 생성
llm = ChatOpenAI(
    model_name=current_config.OPENAI_MODEL_NM,
    temperature=0.7,
    max_tokens=8192,
    api_key=current_config.OPENAI_API_KEY
)
question = "담배를 맛있게 피는 법"
# 프롬프트 템플릿 생성
template = ChatPromptTemplate(
    messages=[
        ("system", "You are a helpful assistant. answer in {country} "),
        ("user", question),
    ],
    memory=chat_memory
)

# 예제 데이터
user_id = "user123"
orgn_id = "org456"
session_id = "session789"

# 프롬프트 생성
formatted_messages = template.format_messages(
    user_id=user_id,
    orgn_id=orgn_id,
    session_id=session_id,
    country="japanese",
)

# OpenAI API를 호출하여 응답 생성
response = llm.generate_response(formatted_messages)
human_message = HumanMessage(question)
chat_memory.add_message(human_message, user_id=user_id, orgn_id=orgn_id, session_id=session_id)
# 응답을 메시지로 저장
ai_message = AIMessage(response)
chat_memory.add_message(ai_message, user_id=user_id, orgn_id=orgn_id, session_id=session_id)

# 출력
print(response)
