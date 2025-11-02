from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.conversation import ConversationStorage
from app.models.user import UserStorage
from app.schemas.conversation import ConversationCreate, ConversationResponse, ConversationUpdate

# 创建对话管理相关路由
router = APIRouter()

@router.get("/", response_model=list[ConversationResponse])
def get_user_conversations(user: str, db: Session = Depends(get_db)):
    """
    获取用户的所有对话
    - 通过用户名查询对应的对话列表
    """
    # 验证用户是否存在
    user_obj = db.query(UserStorage).filter(UserStorage.user == user).first()
    if not user_obj:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 查询该用户的所有对话
    conversations = db.query(ConversationStorage).filter(ConversationStorage.user == user).all()
    return conversations

@router.post("/", response_model=ConversationResponse)
def create_conversation(conversation_data: ConversationCreate, db: Session = Depends(get_db)):
    """
    创建新对话
    - 需要提供对话ID、部分ID、用户名和内容
    """
    # 验证用户是否存在
    user = db.query(UserStorage).filter(UserStorage.user == conversation_data.user).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 检查对话是否已存在
    existing_conversation = db.query(ConversationStorage).filter(
        ConversationStorage.id_conversation == conversation_data.id_conversation,
        ConversationStorage.id_part == conversation_data.id_part,
        ConversationStorage.user == conversation_data.user
    ).first()
    
    if existing_conversation:
        raise HTTPException(status_code=400, detail="对话已存在")
    
    # 创建新对话实例
    new_conversation = ConversationStorage(
        id_conversation=conversation_data.id_conversation,
        id_part=conversation_data.id_part,
        user=conversation_data.user,
        markdown=conversation_data.markdown
    )
    
    # 保存到数据库
    db.add(new_conversation)
    db.commit()
    db.refresh(new_conversation)
    
    return new_conversation

@router.get("/{id_conversation}/{id_part}", response_model=ConversationResponse)
def get_conversation(id_conversation: int, id_part: int, user: str, db: Session = Depends(get_db)):
    """根据对话ID、部分ID和用户名获取特定对话"""
    conversation = db.query(ConversationStorage).filter(
        ConversationStorage.id_conversation == id_conversation,
        ConversationStorage.id_part == id_part,
        ConversationStorage.user == user
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    return conversation

@router.put("/{id_conversation}/{id_part}", response_model=ConversationResponse)
def update_conversation(
    id_conversation: int, 
    id_part: int,
    user: str,
    conversation_data: ConversationUpdate, 
    db: Session = Depends(get_db)
):
    """更新对话内容"""
    # 查询现有对话
    conversation = db.query(ConversationStorage).filter(
        ConversationStorage.id_conversation == id_conversation,
        ConversationStorage.id_part == id_part,
        ConversationStorage.user == user
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    # 更新字段
    if conversation_data.markdown is not None:
        conversation.markdown = conversation_data.markdown
    
    # 提交更改
    db.commit()
    db.refresh(conversation)
    
    return conversation

@router.delete("/{id_conversation}/{id_part}")
def delete_conversation(id_conversation: int, id_part: int, user: str, db: Session = Depends(get_db)):
    """删除对话"""
    conversation = db.query(ConversationStorage).filter(
        ConversationStorage.id_conversation == id_conversation,
        ConversationStorage.id_part == id_part,
        ConversationStorage.user == user
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    # 从数据库删除
    db.delete(conversation)
    db.commit()
    
    return {"message": "对话删除成功"}

@router.get("/{id_conversation}/parts", response_model=list[ConversationResponse])
def get_conversation_parts(id_conversation: int, user: str, db: Session = Depends(get_db)):
    """获取特定对话的所有部分"""
    # 验证用户是否存在
    user_obj = db.query(UserStorage).filter(UserStorage.user == user).first()
    if not user_obj:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 查询该对话的所有部分
    parts = db.query(ConversationStorage).filter(
        ConversationStorage.id_conversation == id_conversation,
        ConversationStorage.user == user
    ).all()
    
    return parts
