import os
import asyncio
from openai import OpenAI, AsyncOpenAI
from typing import Optional, Dict, Any, List, Generator, AsyncGenerator


class ChatOpenAI:
    """
    OpenAI 모델 생성자 클래스.

    Args:
        model_name (str): 사용할 OpenAI 모델의 이름.
        temperature (float): 샘플링 온도.
        max_tokens (Optional[int]): 생성할 최대 토큰 수.
        api_key (Optional[str]): OpenAI API 키. 설정하지 않으면 환경 변수 OPENAI_API_KEY에서 읽어옴.
        base_url (Optional[str]): API 요청을 위한 기본 URL. 프록시나 서비스 에뮬레이터 사용 시 지정.
        **kwargs: 추가적인 매개변수는 API 호출 시 전달됨.
    """

    def __init__(
            self,
            model_name: str,
            temperature: float = 0.7,
            max_tokens: Optional[int] = None,
            api_key: Optional[str] = None,
            base_url: Optional[str] = None,
            **kwargs: Any,
    ) -> None:
        # 환경변수에서 API 키 가져오기
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key is required. Set it via the 'api_key' argument or the 'OPENAI_API_KEY' environment variable."
            )

        # 동기 및 비동기 OpenAI 클라이언트 초기화
        self.client = OpenAI(api_key=self.api_key, base_url=base_url)
        self.async_client = AsyncOpenAI(api_key=self.api_key, base_url=base_url)
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.base_url = base_url
        self.extra_kwargs = kwargs

    def __repr__(self) -> str:
        return (
            f"ChatOpenAI(model={self.model_name}, temperature={self.temperature}, "
            f"max_tokens={self.max_tokens}, api_key={'***' if self.api_key else None}, "
            f"base_url={self.base_url}, extra_kwargs={self.extra_kwargs})"
        )

    def generate_response(self, messages: List[Dict[str, str]]) -> str:
        """
        대화 메시지 목록을 받아 모델의 응답을 생성합니다.

        Args:
            messages (List[Dict[str, str]]): 대화 메시지 목록.

        Returns:
            str: 모델의 응답 메시지.
        """
        try:
            chat_completion = self.client.chat.completions.create(
                messages=messages,
                model=self.model_name,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                **self.extra_kwargs
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"Failed to generate response: {e}")

    def stream_response(self, messages: List[Dict[str, str]]) -> Generator[str, None, None]:
        """
        대화 메시지 목록을 받아 스트리밍 방식으로 모델의 응답을 한 글자씩 생성합니다.

        Args:
            messages (List[Dict[str, str]]): 대화 메시지 목록.

        Yields:
            str: 한 번에 한 글자씩 반환합니다.
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=True,
                **self.extra_kwargs
            )

            for chunk in response:
                if chunk.choices[0].delta.get('content'):
                    content = chunk.choices[0].delta.content
                    for char in content:
                        yield char
        except Exception as e:
            raise RuntimeError(f"Failed to stream response: {e}")

    async def async_generate_response(self, messages: List[Dict[str, str]]) -> str:
        """
        대화 메시지 목록을 비동기적으로 받아 모델의 응답을 생성합니다.

        Args:
            messages (List[Dict[str, str]]): 대화 메시지 목록.

        Returns:
            str: 모델의 응답 메시지.
        """
        try:
            chat_completion = await self.async_client.chat.completions.create(
                messages=messages,
                model=self.model_name,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                **self.extra_kwargs
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"Failed to generate async response: {e}")

    async def async_stream_response(self, messages: List[Dict[str, str]]) -> AsyncGenerator[str, None]:
        """
        대화 메시지 목록을 비동기적으로 받아 스트리밍 방식으로 모델의 응답을 한 글자씩 생성합니다.

        Args:
            messages (List[Dict[str, str]]): 대화 메시지 목록.

        Yields:
            str: 한 번에 한 글자씩 반환합니다.
        """
        try:
            response = await self.async_client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=True,
                **self.extra_kwargs
            )

            async for chunk in response:
                if chunk.choices[0].delta.get('content'):
                    content = chunk.choices[0].delta.content
                    for char in content:
                        yield char
        except Exception as e:
            raise RuntimeError(f"Failed to stream async response: {e}")

