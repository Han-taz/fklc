from typing import List, Dict, Any, Sequence, Literal, Union, Optional, Tuple, Callable
from sql_memory import ChatHistory, BaseMessage, HumanMessage, AIMessage,SQLChatMemory

class ChatPromptTemplate:
    """
    시스템 메시지와 유저 메시지를 포함한 채팅 프롬프트 템플릿 클래스.

    Args:
        messages (List[Union[str, Tuple[str, str]]]): 메시지 템플릿의 리스트.
        template_format (Literal["f-string", "mustache", "jinja2"]): 템플릿 형식. 기본은 "f-string".
        memory (Optional[SQLChatMemory]): 이전 대화 내역을 가져올 수 있는 메모리 인스턴스.
    """

    def __init__(
        self,
        messages: Sequence[Union[str, Tuple[str, str]]],
        template_format: Literal["f-string", "mustache", "jinja2"] = "f-string",
        memory: Optional[SQLChatMemory] = None
    ) -> None:
        self.messages = messages
        self.template_format = template_format
        self.memory = memory

    def format_messages(self, user_id: str, orgn_id: str, session_id: str, max_tokens: int = 1000, **kwargs: Any) -> List[Dict[str, str]]:
        """
        메시지 템플릿을 실제 메시지로 변환합니다.

        Args:
            user_id (str): 유저 ID.
            orgn_id (str): 기관 ID.
            session_id (str): 세션 ID.
            max_tokens (int): 포함할 최대 토큰 수. 기본값은 1000.
            **kwargs: 템플릿 변수를 채우는 데 사용할 값들.

        Returns:
            List[Dict[str, str]]: 채워진 메시지의 리스트.
        """
        formatted_messages = []

        # 메모리에서 대화 내역을 가져와서 추가
        if self.memory:
            memory_messages = self.memory.get_messages_with_token_limit(
                user_id=user_id,
                orgn_id=orgn_id,
                session_id=session_id,
                max_tokens=max_tokens
            )
            formatted_messages.extend(memory_messages)

        # 템플릿 메시지 처리
        for message in self.messages:
            if isinstance(message, str):
                # 기본적으로 유저 메시지로 간주
                formatted_messages.append({"role": "user", "content": message.format(**kwargs)})
            elif isinstance(message, tuple):
                role, template = message
                # 함수 호출을 포함한 동적 템플릿 처리
                content = template.format(**{
                    key: (value(*args) if isinstance(value, tuple) and callable(value[0]) else value)
                    for key, value in kwargs.items()
                })
                formatted_messages.append({"role": role, "content": content})

        return formatted_messages



