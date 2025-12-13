# app/repositories/base.py
"""
基础Repository类
提供通用的CRUD操作
"""
from typing import TypeVar, Type, Generic, List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from app.database import Base

ModelType = TypeVar("ModelType", bound=Base) # type: ignore



class BaseRepository(Generic[ModelType]):
    """基础Repository类"""
    
    def __init__(self, model: Type[ModelType], db: Session):
        """
        初始化Repository
        
        Args:
            model: SQLAlchemy模型类
            db: 数据库会话
        """
        self.model = model
        self.db = db
    
    def get_by_id(self, id: int) -> Optional[ModelType]:
        """
        根据ID获取单个记录
        
        Args:
            id: 记录ID
            
        Returns:
            模型实例或None
        """
        # 注意：不同模型的主键字段名不同
        # 使用getattr来获取主键列名
        primary_key = self.model.__table__.primary_key.columns.keys()[0]
        return self.db.query(self.model).filter(
            getattr(self.model, primary_key) == id
        ).first()
    
    def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100,
        order_by: Optional[str] = None,
        order_desc: bool = False
    ) -> List[ModelType]:
        """
        获取所有记录（分页）
        
        Args:
            skip: 跳过的记录数
            limit: 返回的最大记录数
            order_by: 排序字段
            order_desc: 是否降序
            
        Returns:
            模型实例列表
        """
        query = self.db.query(self.model)
        
        # 排序
        if order_by:
            column = getattr(self.model, order_by, None)
            if column:
                if order_desc:
                    query = query.order_by(desc(column))
                else:
                    query = query.order_by(asc(column))
        
        return query.offset(skip).limit(limit).all()
    
    def create(self, obj_in: Dict[str, Any]) -> ModelType:
        """
        创建新记录
        
        Args:
            obj_in: 包含字段值的字典
            
        Returns:
            创建的模型实例
        """
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    
    def update(self, db_obj: ModelType, obj_in: Dict[str, Any]) -> ModelType:
        """
        更新记录
        
        Args:
            db_obj: 数据库中的模型实例
            obj_in: 包含更新字段的字典
            
        Returns:
            更新后的模型实例
        """
        for field, value in obj_in.items():
            if hasattr(db_obj, field) and value is not None:
                setattr(db_obj, field, value)
        
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    
    def delete(self, db_obj: ModelType) -> ModelType:
        """
        删除记录
        
        Args:
            db_obj: 要删除的模型实例
            
        Returns:
            删除的模型实例
        """
        self.db.delete(db_obj)
        self.db.commit()
        return db_obj
    
    def delete_by_id(self, id: int) -> bool:
        """
        根据ID删除记录
        
        Args:
            id: 记录ID
            
        Returns:
            是否删除成功
        """
        primary_key = self.model.__table__.primary_key.columns.keys()[0]
        db_obj = self.db.query(self.model).filter(
            getattr(self.model, primary_key) == id
        ).first()
        
        if db_obj:
            self.delete(db_obj)
            return True
        return False
    
    def count(self) -> int:
        """
        获取总记录数
        
        Returns:
            记录总数
        """
        return self.db.query(self.model).count()
    
    def exists(self, id: int) -> bool:
        """
        检查记录是否存在
        
        Args:
            id: 记录ID
            
        Returns:
            是否存在
        """
        primary_key = self.model.__table__.primary_key.columns.keys()[0]
        return self.db.query(self.model).filter(
            getattr(self.model, primary_key) == id
        ).first() is not None
    
    def search(
        self, 
        filters: Dict[str, Any],
        skip: int = 0,
        limit: int = 100
    ) -> List[ModelType]:
        """
        根据条件搜索记录
        
        Args:
            filters: 过滤条件字典
            skip: 跳过的记录数
            limit: 返回的最大记录数
            
        Returns:
            匹配的模型实例列表
        """
        query = self.db.query(self.model)
        
        for field, value in filters.items():
            if hasattr(self.model, field):
                if value is None:
                    query = query.filter(getattr(self.model, field).is_(None))
                elif isinstance(value, (list, tuple)):
                    query = query.filter(getattr(self.model, field).in_(value))
                else:
                    query = query.filter(getattr(self.model, field) == value)
        
        return query.offset(skip).limit(limit).all()
    
    def get_or_create(
        self, 
        defaults: Dict[str, Any], 
        **kwargs
    ) -> tuple[ModelType, bool]:
        """
        获取或创建记录
        
        Args:
            defaults: 创建时使用的默认值
            **kwargs: 查找条件
            
        Returns:
            (模型实例, 是否是新创建的)
        """
        instance = self.db.query(self.model).filter_by(**kwargs).first()
        if instance:
            return instance, False
        
        # 合并参数和默认值
        params = {**kwargs, **defaults}
        instance = self.model(**params)
        self.db.add(instance)
        self.db.commit()
        self.db.refresh(instance)
        return instance, True
    
    
    def create_from_instance(self, instance: ModelType) -> ModelType:
        """
        从模型实例创建记录
        
        Args:
            instance: 模型实例
            
        Returns:
            创建的模型实例
        """
        self.db.add(instance)
        self.db.commit()
        self.db.refresh(instance)
        return instance

