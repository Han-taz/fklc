from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import create_engine, Column, Integer, String, Text, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from typing import List, Dict, Optional
import os

Base = declarative_base()

class ChatHistory(Base):
    __tablename__ = 'chat_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), nullable=False)
    orgn_id = Column(String(255), nullable=False)
    session_id = Column(String(255), nullable=False)
    role = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(TIMESTAMP, default=datetime.utcnow)


class BaseMessage:
    """Base class for messages."""
    def __init__(self, content: str) -> None:
        self.content = content
        self.role = None

    def to_chat_history(self, user_id: str, orgn_id: str, session_id: str) -> ChatHistory:
        """Converts the message to a ChatHistory entry."""
        return ChatHistory(
            user_id=user_id,
            orgn_id=orgn_id,
            session_id=session_id,
            role=self.role,
            content=self.content
        )


class HumanMessage(BaseMessage):
    """Represents a message from a human user."""
    def __init__(self, content: str) -> None:
        super().__init__(content)
        self.role = "user"


class AIMessage(BaseMessage):
    """Represents a message from the AI."""
    def __init__(self, content: str) -> None:
        super().__init__(content)
        self.role = "assistant"


class SQLChatMemory:
    """
    SQLAlchemy를 사용하여 MySQL/MariaDB에 대화 내역을 관리하는 클래스.
    동기식 및 비동기식 메서드를 모두 제공합니다.
    """

    def __init__(self, db_url: Optional[str] = None, async_db_url: Optional[str] = None) -> None:
        self.sync_engine = None
        self.async_engine = None
        self.SyncSession = None
        self.AsyncSession = None
        self.use_local_llm = os.getenv('USE_LOCAL_LLM', 'False').lower() in ['true', '1', 't']

        # 토크나이저 설정
        if self.use_local_llm:
            from transformers import AutoTokenizer
            self.tokenizer = AutoTokenizer.from_pretrained("meta-llama/Meta-Llama-3-8B")
        else:
            import tiktoken  # 토큰화 라이브러리
            self.tokenizer = tiktoken.get_encoding("cl100k_base")  # 예: GPT-3.5/4의 기본 토크나이저 사용

        if db_url:
            self.create_sync_engine(db_url)
        if async_db_url:
            self.create_async_engine(async_db_url)

    def create_sync_engine(self, db_url: str) -> None:
        """동기식 엔진을 생성합니다."""
        self.sync_engine = create_engine(db_url)
        Base.metadata.create_all(self.sync_engine)
        self.SyncSession = sessionmaker(bind=self.sync_engine)

    def create_async_engine(self, async_db_url: str) -> None:
        """비동기식 엔진을 생성합니다."""
        self.async_engine = create_async_engine(async_db_url, echo=True)
        self.AsyncSession = sessionmaker(
            bind=self.async_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

    # 동기 메서드
    def add_message(self, message: BaseMessage, user_id: str, orgn_id: str, session_id: str) -> None:
        """메시지를 추가합니다."""
        if not self.SyncSession:
            raise ValueError("Sync engine is not initialized. Call `create_sync_engine` first.")
        session = self.SyncSession()
        chat_history_entry = message.to_chat_history(user_id, orgn_id, session_id)
        session.add(chat_history_entry)
        session.commit()
        session.close()

    def add_messages(self, messages: List[BaseMessage], user_id: str, orgn_id: str, session_id: str) -> None:
        """여러 메시지를 동기식으로 한 번에 추가합니다."""
        if not self.SyncSession:
            raise ValueError("Sync engine is not initialized. Call `create_sync_engine` first.")

        session = self.SyncSession()
        try:
            for message in messages:
                chat_history_entry = message.to_chat_history(user_id, orgn_id, session_id)
                session.add(chat_history_entry)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_history(self, user_id: str, orgn_id: str, session_id: str) -> List[Dict[str, str]]:
        """대화 내역을 가져옵니다."""
        if not self.SyncSession:
            raise ValueError("Sync engine is not initialized. Call `create_sync_engine` first.")
        session = self.SyncSession()
        history = session.query(ChatHistory).filter_by(
            user_id=user_id,
            orgn_id=orgn_id,
            session_id=session_id
        ).order_by(ChatHistory.timestamp.asc()).all()
        session.close()
        return [{"role": record.role, "content": record.content} for record in history]

    def get_messages_with_token_limit(self, user_id: str, orgn_id: str, session_id: str, max_tokens: int) -> List[
        Dict[str, str]]:
        """지정된 토큰 수 이내의 대화 내역을 가져옵니다."""
        if not self.SyncSession:
            raise ValueError("Sync engine is not initialized. Call `create_sync_engine` first.")

        session = self.SyncSession()
        history = session.query(ChatHistory).filter_by(
            user_id=user_id,
            orgn_id=orgn_id,
            session_id=session_id
        ).order_by(ChatHistory.timestamp.asc()).all()
        session.close()

        total_tokens = 0
        limited_messages = []

        for record in history:
            content_tokens = self._count_tokens(record.content)
            if total_tokens + content_tokens > max_tokens:
                break
            total_tokens += content_tokens
            limited_messages.append({"role": record.role, "content": record.content})

        return limited_messages

    def _count_tokens(self, text: str) -> int:
        """텍스트의 토큰 수를 계산합니다."""
        if self.use_local_llm:
            tokens = self.tokenizer.tokenize(text)
            return len(tokens)
        else:
            return len(self.tokenizer.encode(text))

    def clear_history(self, user_id: str, orgn_id: str, session_id: str) -> None:
        """대화 내역을 삭제합니다."""
        if not self.SyncSession:
            raise ValueError("Sync engine is not initialized. Call `create_sync_engine` first.")
        session = self.SyncSession()
        session.query(ChatHistory).filter_by(
            user_id=user_id,
            orgn_id=orgn_id,
            session_id=session_id
        ).delete()
        session.commit()
        session.close()

    # 비동기 메서드
    async def aadd_message(self, message: BaseMessage, user_id: str, orgn_id: str, session_id: str) -> None:
        """메시지를 비동기적으로 추가합니다."""
        if not self.AsyncSession:
            raise ValueError("Async engine is not initialized. Call `create_async_engine` first.")
        async with self.AsyncSession() as session:
            async with session.begin():
                chat_history_entry = message.to_chat_history(user_id, orgn_id, session_id)
                session.add(chat_history_entry)
                await session.commit()

    async def aadd_messages(self, messages: List[BaseMessage], user_id: str, orgn_id: str, session_id: str) -> None:
        """여러 메시지를 비동기식으로 한 번에 추가합니다."""
        if not self.AsyncSession:
            raise ValueError("Async engine is not initialized. Call `create_async_engine` first.")

        async with self.AsyncSession() as session:
            try:
                async with session.begin():
                    for message in messages:
                        chat_history_entry = message.to_chat_history(user_id, orgn_id, session_id)
                        session.add(chat_history_entry)
                    await session.commit()
            except Exception as e:
                await session.rollback()
                raise e

    async def aget_history(self, user_id: str, orgn_id: str, session_id: str) -> List[Dict[str, str]]:
        """대화 내역을 비동기적으로 가져옵니다."""
        if not self.AsyncSession:
            raise ValueError("Async engine is not initialized. Call `create_async_engine` first.")
        async with self.AsyncSession() as session:
            result = await session.execute(
                session.query(ChatHistory).filter_by(
                    user_id=user_id,
                    orgn_id=orgn_id,
                    session_id=session_id
                ).order_by(ChatHistory.timestamp.asc())
            )
            history = result.scalars().all()
            return [{"role": record.role, "content": record.content} for record in history]

    async def aget_messages_with_token_limit(self, user_id: str, orgn_id: str, session_id: str, max_tokens: int) -> \
    List[Dict[str, str]]:
        """지정된 토큰 수 이내의 대화 내역을 비동기적으로 가져옵니다."""
        if not self.AsyncSession:
            raise ValueError("Async engine is not initialized. Call `create_async_engine` first.")

        async with self.AsyncSession() as session:
            result = await session.execute(
                session.query(ChatHistory).filter_by(
                    user_id=user_id,
                    orgn_id=orgn_id,
                    session_id=session_id
                ).order_by(ChatHistory.timestamp.asc())
            )
            history = result.scalars().all()

        total_tokens = 0
        limited_messages = []

        for record in history:
            content_tokens = self._count_tokens(record.content)
            if total_tokens + content_tokens > max_tokens:
                break
            total_tokens += content_tokens
            limited_messages.append({"role": record.role, "content": record.content})

        return limited_messages

    async def aclear_history(self, user_id: str, orgn_id: str, session_id: str) -> None:
        """대화 내역을 비동기적으로 삭제합니다."""
        if not self.AsyncSession:
            raise ValueError("Async engine is not initialized. Call `create_async_engine` first.")
        async with self.AsyncSession() as session:
            await session.execute(
                session.query(ChatHistory).filter_by(
                    user_id=user_id,
                    orgn_id=orgn_id,
                    session_id=session_id
                ).delete()
            )
            await session.commit()


"""
# HumanMessage 사용 예시
human_message = HumanMessage("Hello, how can I help you?")
chat_memory.add_message(human_message, user_id="user1", orgn_id="org1", session_id="session1")

# AIMessage 사용 예시
ai_message = AIMessage("I am here to assist you with your questions.")
chat_memory.add_message(ai_message, user_id="user1", orgn_id="org1", session_id="session1")

"""